import sys

from PyQt5 import QtCore
from PyQt5.QtWidgets import QDockWidget, QAbstractItemView
from qtconsole.inprocess import QtInProcessKernelManager
from qtconsole.rich_jupyter_widget import RichJupyterWidget

from praatkatili.canvas import PlotCanvas
from praatkatili.config import *
from praatkatili.dock import PlotDock, ResourceDock
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
        self.consoleDock = dock = QDockWidget(objectName="consoleDock")
        dock.setMinimumHeight(80)
        dock.setMinimumWidth(500)
        dock.setWindowTitle("IPython Shell")
        dock.setFeatures(DOCK_FEATURES)
        # self.consoleDock.setLayout(QtWidgets.QHBoxLayout())
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, dock)
        dock.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.console = RichJupyterWidget(name="console")
        self.console.font_size = 7
        dock.setWidget(self.console)
        self.setup_ipython()

    def find_docks(self, name=None):
        return self.findChildren(QDockWidget, name)

    def setup_ipython(self):
        """
        Sets up the ipython shell for the relevant docks. 
        :return: 
        """
        self.console.kernel_manager = kernel_manager = QtInProcessKernelManager()
        kernel_manager.start_kernel(show_banner=True)
        kernel_manager.kernel.gui = 'qt'
        self.console.kernel_client = kernel_client = kernel_manager.client()
        kernel_client.start_channels()

        def stop():
            kernel_client.stop_channels()
            kernel_manager.shutdown_kernel()
            # guisupport.get_app_qt().exit()

        self.console.exit_requested.connect(stop)
        self.push_vars({"KatilInstance": self})
        self.console.show()
        self.inject_globals()
        self.inject_debugs()

    def setup_browser(self):
        """
        Sets up the resource browser.
        :return: 
        """
        self.browserDock = dock = QDockWidget(objectName="browserDock")
        dock.setMinimumWidth(300)
        dock.setMinimumHeight(125)
        dock.setFeatures(DOCK_FEATURES)
        dock.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        dock.setWindowTitle("File Browser")
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock)

        self.file_view = view = QtWidgets.QTreeView()
        dock.setWidget(self.file_view)

        self.file_model.setRootPath(QtCore.QDir.homePath())
        view.setModel(self.file_model)
        view.setRootIndex(self.file_model.index(QtCore.QDir.homePath()))

        view.setAutoScroll(True)
        view.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        view.setAutoExpandDelay(0)
        view.doubleClicked.connect(self.open_file)
        from PyQt5.QtCore import QTimer
        self.t = t = QTimer()
        t.singleShot(500, self.show_home)

    # def data_changed(self, topl, bottomr, roles):
    #     print(topl.data())
    #     print(self.resource_model.data(topl))
    #     # print(str(bottomr))
    #     # print(str(roles))

    def show_folder(self, folder=os.path.expanduser("~/Dropbox/MarcosLemurData")):
        """
        Expands and shows a folder in the resource browser. 
        :param folder: 
        :return: 
        """
        r = self.file_model.index(folder)
        self.file_view.setExpanded(r, True)
        self.file_view.setCurrentIndex(r)
        self.file_view.scrollTo(r, QAbstractItemView.PositionAtTop)

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
            resource.open()
            r, r2, r3, r4 = QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem()
            # r.setData(resource.alias)
            r.setText(resource.alias)
            # def change_alias(*args):
            #     print(args)
            # r.dataChanged.connect(change_alias)
            r2.setText(resource.__class__.__name__)
            r2.setEditable(False)
            try:
                r3.setText(resource.path)
            except AttributeError:
                r3.setText("N/A")
            r3.setEditable(False)
            r4.setText(str(resource.data))
            r4.setEditable(False)
            [r.setData(resource) for r in (r, r2, r3, r4)]
            # r.setText(str(resource))
            self.resource_model.appendRow([r, r2, r3, r4])
        except KeyError:
            raise UnknownResourceTypeError(path)

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
        self.plots.append(dock)
        self.plot_counter += 1
        return tab_group

    def push_vars(self, variableDict):
        """
        Given a dictionary containing name / value pairs, push those variables
        to the Jupyter console widget
        """
        self.console.kernel_manager.kernel.shell.push(variableDict)

    def clear(self):
        """
        Clears the terminal
        """
        self.console._control.clear()

        # self.kernel_manager

    def print_text(self, text):
        """
        Prints some plain text to the console
        """
        self.console._append_plain_text(text)

    def execute_command(self, command):
        """
        Execute a command in the frame of the console widget
        """
        self.console._execute(command, False)

    def inject_globals(self):
        """
        Inject the globals() dict into the IPython kernel
        under the key '_injected'
        :return:
        """
        self.push_vars({"_injected": globals()})
        self.execute_command("from PyQt5.QtWidgets import *")

    def inject_debugs(self):
        self.push_vars({'canvas': self.findChildren(PlotCanvas)})


if __name__ == "__main__":
    qapp = QtWidgets.QApplication(sys.argv)
    global main_widget
    main_widget = Katil()
    sys.exit(qapp.exec_())
