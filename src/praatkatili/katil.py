import sys

from PyQt5 import QtCore
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QDockWidget, QMessageBox, QAction

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
        #
        self.file_model = QtWidgets.QFileSystemModel()
        self.resourceDock = self.browserDock = self.consoleDock = None

        self.setup_main_window()
        self.setup_widgets()
        self.show()

        # plot actions
        line = QAction("Line plot", self)
        scatter = QAction("Scatter plot", self)
        line.triggered.connect(self.add_line_plot)
        self.plot_actions = [line, scatter]

        # resource actions
        add_file = QAction("Add file as resource", self)
        remove_resource = QAction("Remove resource", self)
        self.resource_actions = [add_file, remove_resource]

        self.addActions(self.plot_actions + self.resource_actions)

        settings = QSettings(QSettings.IniFormat, QSettings.UserScope,
                             "KeremEryilmaz", "PraatKatili");
        # settings.setValue("windowState", self.saveState());
        try:
            geo = settings.value("Katil/geometry")
            state = settings.value("Katil/windowState")
        except AttributeError:
            pass
        if geo is not None:
            self.restoreGeometry(geo)
            self.restoreState(state)
            print("Restored window state.")
        ress = settings.value("Katil/resources")
        if ress:
            counter = 0
            for res in ress:
                res.open()
                self._add_resource(res)
                counter += 1
            print("Restored {} file resources.".format(counter))

    def closeEvent(self, event):
        settings = QSettings(QSettings.IniFormat, QSettings.UserScope,
                             "KeremEryilmaz", "PraatKatili");
        settings.setValue("Katil/geometry", self.saveGeometry());
        settings.setValue("Katil/windowState", self.saveState());

        # serialize file resources
        settings.setValue("Katil/resources", self.resources)

        super(Katil, self).closeEvent(event);

    def add_line_plot(self):
        selected = self.resource_view.currentIndex()
        self.add_plot()
        dock = self.plots[-1]
        res = self.resource_model.itemFromIndex(selected).data()
        dock.canvas.plot_line(res.data, res.alias)

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
        self.consoleDock = dock = IPythonDock(objectName="consoleDock")
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
        self.file_view.doubleClicked.connect(self.add_file_resource)

    def add_file_resource(self, index):
        """
        Adds the selected file resource to resource list.
        :param index: 
        :return: 
        """
        path = self.file_model.filePath(index)
        self.open_file(path)

    def open_file(self, path):
        """
        Opens the supported file types, as described by the classes in praatkiller.resource module. 
        :param index: 
        :return: 
        """
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
            self._add_resource(resource)
        except KeyError:
            ext = os.path.splitext(path)[1]
            QMessageBox.critical(self,
                                 "Unknown type: {}".format(ext),
                                 "Unknown type {} at path: \n{}".format(ext, path))
        except DuplicateFileResourceError:
            QMessageBox.critical(self,
                                 "Duplicate resource error",
                                 "A resource with this path already exists: \n{}".format(path))

    def _add_resource(self, resource):
        self.resources.append(resource)
        self.resourceDock.add_resource(resource)


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

        dock.xshift_changed.connect(dock.canvas.set_xshift)
        dock.yshift_changed.connect(dock.canvas.set_yshift)
        dock.xzoom_changed.connect(dock.canvas.set_xzoom)
        dock.yzoom_changed.connect(dock.canvas.set_yzoom)
        self.plots.append(dock)
        self.plot_counter += 1
        return tab_group



if __name__ == "__main__":
    qapp = QtWidgets.QApplication(sys.argv)
    qapp.setOrganizationName("KeremEryilmaz")
    qapp.setApplicationName("PraatKatili")
    qapp.setApplicationDisplayName("Praat Katili")
    global main_widget
    main_widget = Katil()
    sys.exit(qapp.exec_())
