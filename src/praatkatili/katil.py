import os
import sys

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDockWidget
from PyQt5.QtGui import QStandardItemModel
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.figure import Figure
# import matplotlib.pyplot as plt
from qtconsole.inprocess import QtInProcessKernelManager
# from IPython.lib import guisupport
from qtconsole.rich_jupyter_widget import RichJupyterWidget

from praatkatili.canvas import PlotCanvas
from praatkatili.resource import *

main_ui = "res/mainwindow.ui"


class Katil(QtWidgets.QMainWindow):
    def __init__(self):
        super(Katil, self).__init__()
        self.plots = []
        self.plot_counter = 1
        self.tab_groups = []
        #
        self.file_model = QtWidgets.QFileSystemModel()
        self.dock_features = QtWidgets.QDockWidget.AllDockWidgetFeatures

        self.setup_main_window()
        self.setup_widgets()
        self.show()

    def setup_main_window(self):
        # self.setLayout(QtWidgets.QFormLayout())
        self.setDockOptions(QtWidgets.QMainWindow.AllowNestedDocks | \
                            QtWidgets.QMainWindow.AllowTabbedDocks)
        # w = QtWidgets.QWidget(self)
        # w.setVisible(False)
        # self.setCentralWidget(w)

    def setup_widgets(self):
        self.setup_console()
        self.setup_browser()
        self.setup_resources()
        self.add_plot()
        self.add_plot(0)
        self.add_plot()

    def setup_console(self):
        self.consoleDock = QDockWidget(objectName="consoleDock")
        self.consoleDock.setMinimumHeight(80)
        self.consoleDock.setMinimumWidth(500)
        self.consoleDock.setWindowTitle("IPython Shell")
        self.consoleDock.setFeatures(self.dock_features)
        # self.consoleDock.setLayout(QtWidgets.QHBoxLayout())
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.consoleDock)
        self.consoleDock.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.console = RichJupyterWidget(name="console")
        self.console.font_size = 7
        self.consoleDock.setWidget(self.console)
        self.setup_ipython()

    def find_docks(self, name=None):
        return self.findChildren(QDockWidget, name)

    def setup_ipython(self):
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
        self.browserDock = QDockWidget(objectName="browserDock")
        self.browserDock.setMinimumWidth(300)
        self.browserDock.setMinimumHeight(125)
        self.browserDock.setFeatures(self.dock_features)
        self.browserDock.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.browserDock.setWindowTitle("File Browser")
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.browserDock)

        self.file_view = QtWidgets.QTreeView()
        self.file_model.setRootPath(QtCore.QDir.homePath())
        self.file_view.setModel(self.file_model)
        self.file_view.setRootIndex(self.file_model.index(QtCore.QDir.homePath()))
        self.file_view.setCurrentIndex(
                self.file_model.index("/Users/Kerem/Dropbox"))
        self.browserDock.setWidget(self.file_view)
        self.file_view.doubleClicked.connect(self.open_file)

    def open_file(self, index):
        row = index.row()
        path = os.path.join(os.path.expanduser('~'), index.sibling(row, 0).data())
        print(path)
        if os.path.isdir(path):
            return
        try:
            ftype = FileTypes["*" + os.path.splitext(path)[1]]
            resource = ftype(path)
            resource.open()
            r = QStandardItem()
            r.setData(resource)
            self.resource_model.appendRow(r)
        except KeyError:
            raise UnknownResourceTypeError(path)

    def setup_resources(self):
        self.resourceDock = QDockWidget(objectName="resourceDock")
        self.resourceDock.setMinimumWidth(300)
        self.resourceDock.setMinimumHeight(125)
        self.resourceDock.setFeatures(self.dock_features)
        self.resourceDock.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.resourceDock.setWindowTitle("Resources")
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.resourceDock)

        self.resource_view = QtWidgets.QTreeView()
        self.resource_model = QStandardItemModel()
        self.resource_view.setModel(self.resource_model)
        self.resourceDock.setWidget(self.resource_view)

    def add_plot(self, tab_group=None):
        dock = QDockWidget(objectName="plot{}".format(self.plot_counter))
        dock.setFeatures(self.dock_features)
        dock.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        dock.tab_group = tab_group

        canvas = PlotCanvas()
        dock.setWidget(canvas)
        dock.setWindowTitle("{} (plot{:>2})".format(canvas.axes.get_title(),
                                                    self.plot_counter))
        if tab_group is not None:
            for p in filter(lambda x: x.tab_group == tab_group, self.plots):
                self.tabifyDockWidget(p, dock)
        else:
            try:
                self.tab_groups.append(max(tab_group)+1)
            except TypeError:
                self.tab_groups.append(0)
            dock.tab_group = max(self.tab_groups)
        canvas.dock = dock
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
