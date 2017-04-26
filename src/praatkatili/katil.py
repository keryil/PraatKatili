import sys

from PyQt5 import QtCore
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QDockWidget, QMessageBox, QProgressDialog

from praatkatili.config import *
from praatkatili.dock import PlotDock, ResourceDock, FileBrowserDock, IPythonDock, NotebookDock
from praatkatili.resources import *
from praatkatili.util import sanitize_alias
import pandas as pd


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
        scatter.triggered.connect(self.add_scatter_plot)
        self.plot_actions = [line, scatter]

        # resource actions
        add_file = QAction("Add file as resource", self)
        remove_resource = QAction("Remove resource", self)
        self.resource_actions = [add_file, remove_resource]
        self.addActions(self.plot_actions + self.resource_actions)

        self.restoreSettings()

    def restoreSettings(self):
        progress = QProgressDialog("Restoring resources...", "Cancel", 0, 100)
        progress.setMinimumDuration(1000)
        progress.setModal(True)

        self.settings = settings = QSettings(QSettings.IniFormat, QSettings.UserScope,
                                             "KeremEryilmaz", "PraatKatili")
        ress = settings.value("Katil/resources")
        if ress:
            counter = 0
            for res in ress:
                res.open()
                self._add_resource(res)
                counter += 1
                progress.setValue(counter * 30 / len(ress))
            print("Restored {} file resources.".format(counter))
        progress.setLabelText("Restoring plots")
        plots = settings.value("Katil/plots")
        if plots:
            counter = 0
            for tab_group, p in plots:
                self.add_plot(tab_group=tab_group,
                              blank=True)
                self.plots[-1].canvas.from_dict(p)
                counter += 1
                progress.setValue(30 + counter * 50 / len(plots))
            print("Restored {} plots.".format(counter))
        progress.setLabelText("Restoring window geometry and state")
        try:
            geo = settings.value("Katil/geometry")
            state = settings.value("Katil/windowState")
        except AttributeError:
            pass
        if geo is not None:
            self.restoreGeometry(geo)
            self.restoreState(state)
            print("Restored window state.")
        progress.setValue(100)

    def closeEvent(self, event):
        self.save_settings()
        self.notebookDock.stop_server()
        super(Katil, self).closeEvent(event);

    def save_settings(self):
        progress = QProgressDialog("Saving geometry...", "Cancel", 0, 100)
        progress.setMinimumDuration(500)
        progress.setModal(True)
        # progress.show()

        settings = QSettings(QSettings.IniFormat, QSettings.UserScope,
                             "KeremEryilmaz", "PraatKatili");
        settings.setValue("Katil/geometry", self.saveGeometry());
        progress.setValue(10)
        progress.setLabelText("Saving window state...")
        settings.setValue("Katil/windowState", self.saveState());
        progress.setValue(20)
        progress.setLabelText("Saving resources...")
        settings.setValue("Katil/resources", self.resources)
        progress.setValue(50)
        plots = []
        progress.setLabelText("Saving plots...")
        for i, p in enumerate(self.plots):
            plots.append((p.tab_group, p.canvas.to_dict()))
            progress.setValue(50 + (i + 1) * (45 / len(self.plots)))
        settings.setValue("Katil/plots", plots)
        progress.setValue(100)

    def delete_plot(self, dock):
        """
        Permanently deletes a plot, so that it doesn't get saved with the session at all. 
        :return: 
        """
        i = self.plots.index(dock)
        self.plots = self.plots[:i] + self.plots[i + 1:]
        dock.close()

    def add_line_plot(self):
        selected = self.resource_view.currentIndex()
        self.add_plot(True)
        dock = self.plots[-1]
        dock.canvas.clear()
        res = self.resource_model.itemFromIndex(selected).data()
        dock.canvas.plot_line(res.data, res.alias)
        dock.canvas.axes.autoscale()
        dock.canvas.recenter()

    def add_scatter_plot(self):
        selected = self.resource_view.currentIndex()
        self.add_plot(True)
        dock = self.plots[-1]
        dock.canvas.clear()
        res = self.resource_model.itemFromIndex(selected).data()
        dock.canvas.plot_scatter(res.data, res.alias)
        dock.canvas.axes.autoscale()
        dock.canvas.recenter()

    def setup_main_window(self):
        self.setDockOptions(DOCK_OPTIONS)

    def setup_widgets(self):
        """
        Initializes the UI.
        :return: 
        """
        self.setup_jupyter_notebook()
        self.setup_console()
        self.setup_file_browser()
        self.setup_resources()

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

    def setup_jupyter_notebook(self):
        self.notebookDock = dock = NotebookDock(objectName="notebookDock",
                                                main_window=self)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)

    def setup_file_browser(self):
        """
        Sets up the file browser.
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
        """
        Adds a generic resource to the resources list, and adds it 
        to the ipython namespace.
        :param resource: 
        :return: 
        """
        found = self.resource_model.findItems(resource.alias)
        if len(found) > 0:
            resource.alias += "_{}".format(len(found))
        self.resources.append(resource)
        self.resourceDock.add_resource(resource)
        self.consoleDock.push_vars({sanitize_alias(resource.alias): resource})

    def _delete_resource(self, resource):
        """
        Deletes a generic resource from the resources list, and removes 
        it from the ipython namespace.
        :param resource: 
        :return: 
        """
        i = self.resources.index(resource.data())
        self.resources = self.resources[:i] + self.resources[i + 1:]
        var_name = sanitize_alias(resource.data().alias)
        self.resourceDock.delete_resource(resource)
        self.consoleDock.delete_var(var_name)

    def setup_resources(self):
        """
        Sets up the resource dock. 
        :return: 
        """
        self.resourceDock = ResourceDock(objectName="resourceDock", main_window=self)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.resourceDock)
        self.resource_view, self.resource_model = self.resourceDock.view_and_model()
        self.resourceDock.setWidget(self.resource_view)

    def add_plot(self, tab_group=None, blank=False):
        """
        Creates and adds a new plot dock, optionally belonging to a tab group.
        :param tab_group: 
        :return: 
        """
        dock = PlotDock(objectName="plot{}".format(self.plot_counter),
                        main_window=self,
                        tab_group=tab_group,
                        blank=blank)

        dock.xshift_changed.connect(dock.canvas.set_xshift)
        dock.yshift_changed.connect(dock.canvas.set_yshift)
        dock.xzoom_changed.connect(dock.canvas.set_xzoom)
        dock.yzoom_changed.connect(dock.canvas.set_yzoom)
        dock.frame.slider_zoom_y.setValue(150)
        dock.frame.slider_zoom_x.setValue(150)
        dock.frame.slider_shift_y.setValue(0)
        dock.frame.slider_shift_x.setValue(0)
        self._add_plot(dock, tab_group)

    def _add_plot(self, dock, tab_group):
        """
        Adds the given plot dock to the window and puts it in 
        the right tab group.
        :param dock: 
        :param tab_group: 
        :return: 
        """
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

        self.plots.append(dock)
        self.plot_counter += 1


if __name__ == "__main__":
    qapp = QtWidgets.QApplication(sys.argv)
    qapp.setOrganizationName("KeremEryilmaz")
    qapp.setApplicationName("PraatKatili")
    qapp.setApplicationDisplayName("Praat Katili")
    qapp.setWheelScrollLines(20)
    global main_widget
    main_widget = Katil()
    sys.exit(qapp.exec_())
