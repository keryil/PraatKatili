import sys

from PyQt5 import QtCore
from PyQt5.QtWidgets import QDockWidget, QMessageBox

from praatkatili.config import *
from praatkatili.dock import PlotDock, ResourceDock, FileBrowserDock, IPythonDock
from praatkatili.resource import *


class Katil(QtWidgets.QMainWindow):
    def __init__(self):
        super(Katil, self).__init__()
        self.plots = []
        self.plot_counter = 1
        self.tab_groups = []
        self.resources = []

        self.file_model = QtWidgets.QFileSystemModel()
        self.resourceDock = self.browserDock = self.consoleDock = None

        self.setup_main_window()
        self.setup_widgets()
        self.show()

    def setup_main_window(self):
        self.setDockOptions(DOCK_OPTIONS)

    def setup_widgets(self):
        """
        Initializes the UI.
        :return: 
        """
        self.setup_console()
        self.setup_browser()
        self.setup_resources()
        self.add_plot()
        self.add_plot(0)
        self.add_plot()

    def setup_console(self):
        """
        Sets up the dock containing IPython shell.
        :return: 
        """
        self.consoleDock = dock = IPythonDock()
        dock.setup_ipython(self)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)
        self.console = dock.console
        dock.inject_globals(globals())

    def find_docks(self, name=None):
        return self.findChildren(QDockWidget, name)

    def setup_browser(self):
        """
        Sets up the resource browser.
        :return: 
        """
        self.browserDock = dock = FileBrowserDock(objectName="browserDock", file_model=self.file_model)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)
        self.file_view, _ = dock.view_and_model()
        dock.setWidget(self.file_view)

        self.file_model.setRootPath(QtCore.QDir.homePath())
        self.file_view.doubleClicked.connect(self.open_file)


    def open_file(self, index):
        """
        Opens the supported file types, as described by the classes in praatkiller.resource module. 
        :param index: 
        :return: 
        """
        path = self.file_model.filePath(index)
        try:
            ftype = FileTypes["*" + os.path.splitext(path)[1]]
            resource = ftype(path, alias=os.path.split(path)[-1])

            def check_dup(item):
                try:
                    return item.path == path
                except AttributeError:
                    return False

            if any(map(check_dup, self.resources)):
                raise DuplicateFileResourceError()

            resource.open()
            self.resources.append(resource)
            self.resourceDock.add_resource(resource)
        except KeyError:
            ext = os.path.splitext(path)[1]
            QMessageBox.critical(self,
                                 "Unknown type: {}".format(ext),
                                 "Unknown type {} at path: \n{}".format(ext, path))
        except DuplicateFileResourceError:
            QMessageBox.critical(self,
                                 "Duplicate resource error",
                                 "A resource with this path already exists: \n{}".format(path))

    def setup_resources(self):
        """
        Sets up the resource dock. 
        :return: 
        """
        self.resourceDock = ResourceDock(objectName="resourceDock")
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.resourceDock)
        self.resource_view, self.resource_model = self.resourceDock.view_and_model()
        self.resourceDock.setWidget(self.resource_view)

    def add_plot(self, tab_group=None):
        """
        Adds a new plot dock, optionally belonging to a tab group.
        :param tab_group: 
        :return: 
        """
        dock = PlotDock(objectName="plot{}".format(self.plot_counter),
                        main_window=self,
                        tab_group=tab_group)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        if tab_group is not None:
            for p in filter(lambda x: x.tab_group == tab_group, self.plots):
                self.tabifyDockWidget(p, dock)
        else:
            try:
                self.tab_groups.append(max(tab_group) + 1)
            except TypeError:
                self.tab_groups.append(0)
            dock.tab_group = max(self.tab_groups)

        def print_hello(*args):
            print("Hello", args)

        dock.xshift_changed.connect(print_hello)
        self.plots.append(dock)
        self.plot_counter += 1
        return tab_group



if __name__ == "__main__":
    qapp = QtWidgets.QApplication(sys.argv)
    global main_widget
    main_widget = Katil()
    sys.exit(qapp.exec_())
