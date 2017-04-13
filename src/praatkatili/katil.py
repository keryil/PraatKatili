import os
import sys

from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QDockWidget, QAbstractItemView
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
        self.resources = []
        #
        self.file_model = QtWidgets.QFileSystemModel()
        self.dock_features = QtWidgets.QDockWidget.AllDockWidgetFeatures

        self.setup_main_window()
        self.setup_widgets()
        self.show()

    def setup_main_window(self):
        # self.setLayout(QtWidgets.QGridLayout())
        self.setDockOptions((QtWidgets.QMainWindow.AllowNestedDocks |
                             QtWidgets.QMainWindow.AllowTabbedDocks |
                             QtWidgets.QMainWindow.AnimatedDocks) &
                            ~QtWidgets.QMainWindow.ForceTabbedDocks)
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
        self.consoleDock = dock = QDockWidget(objectName="consoleDock")
        dock.setMinimumHeight(80)
        dock.setMinimumWidth(500)
        dock.setWindowTitle("IPython Shell")
        dock.setFeatures(self.dock_features)
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
        self.browserDock = dock = QDockWidget(objectName="browserDock")
        dock.setMinimumWidth(300)
        dock.setMinimumHeight(125)
        dock.setFeatures(self.dock_features)
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
        t.singleShot(500, self.showHome)

    # def data_changed(self, topl, bottomr, roles):
    #     print(topl.data())
    #     print(self.resource_model.data(topl))
    #     # print(str(bottomr))
    #     # print(str(roles))

    def showHome(self):
        p = os.path.expanduser("~/Dropbox/MarcosLemurData")
        print(p)
        r = self.file_model.index(p)
        self.file_view.setExpanded(r, True)
        self.file_view.setCurrentIndex(r)
        self.file_view.scrollTo(r, QAbstractItemView.PositionAtTop)

    def open_file(self, index):
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
        self.resourceDock = QDockWidget(objectName="resourceDock")
        self.resourceDock.setMinimumWidth(300)
        self.resourceDock.setMinimumHeight(125)
        self.resourceDock.setFeatures(self.dock_features)
        self.resourceDock.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.resourceDock.setWindowTitle("Resources")
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.resourceDock)

        self.resource_view = QtWidgets.QTreeView()
        self.resource_model = QStandardItemModel()
        self.resource_model.setColumnCount(4)
        self.resource_model.setHorizontalHeaderLabels(["Alias",
                                                       "Type",
                                                       "Path",
                                                       "Value"])
        self.resource_view.setModel(self.resource_model)
        # self.resource_view.dataChanged = self.data_changed
        self.resourceDock.setWidget(self.resource_view)

    def add_plot(self, tab_group=None):
        # dock window
        dock = QDockWidget(objectName="plot{}".format(self.plot_counter))
        dock.setFeatures(self.dock_features)
        dock.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        # dock.setLayout(QtWidgets.QFormLayout())
        dock.tab_group = tab_group
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)

        expand = QtWidgets.QSizePolicy.Expanding
        maximum = QtWidgets.QSizePolicy.Maximum

        # scroll area in dock window
        sc = QtWidgets.QScrollArea()
        sc.setAlignment(QtCore.Qt.AlignCenter)
        sc.setLayout(QtWidgets.QFormLayout())
        sc.setSizePolicy(expand, expand)
        dock.setWidget(sc)

        # frame within scroll area
        f = QtWidgets.QWidget()
        f.setLayout(QtWidgets.QFormLayout())
        f.setSizePolicy(expand, expand)

        # canvas on frame
        canvas = PlotCanvas(f)
        canvas.setSizePolicy(expand, expand)
        sc.setWidget(f)
        f.setGeometry(canvas.geometry())
        # (canvas.geometry().height() + 15)
        sc.setGeometry(f.geometry())
        dock.setWindowTitle("{} (plot{:>2})".format(canvas.axes.get_title(),
                                                    self.plot_counter))
        if tab_group is not None:
            for p in filter(lambda x: x.tab_group == tab_group, self.plots):
                self.tabifyDockWidget(p, dock)
        else:
            try:
                self.tab_groups.append(max(tab_group) + 1)
            except TypeError:
                self.tab_groups.append(0)
            dock.tab_group = max(self.tab_groups)
        canvas.dock = dock
        self.plots.append(dock)
        self.plot_counter += 1
        self.setup_sliders(canvas, f)

        return tab_group

    def setup_sliders(self, canvas, f):
        g = canvas.geometry()
        expand = QtWidgets.QSizePolicy.Expanding
        maximum = QtWidgets.QSizePolicy.Maximum

        f.slider_zoom_y = QtWidgets.QSlider(QtCore.Qt.Vertical, f)
        f.slider_zoom_y.setSizePolicy(expand, expand)
        f.slider_zoom_y.setGeometry(2, 46, 22, g.height())
        f.slider_zoom_y.setValue(50)
        def yzoom_change(*args, **kwargs):
            canvas.axes.set
            print(f.slider_zoom_y.value())
        f.slider_zoom_y.sliderReleased.connect(yzoom_change)

        f.slider_shift_y = QtWidgets.QSlider(QtCore.Qt.Vertical, f)
        f.slider_shift_y.setSizePolicy(expand, expand)
        f.slider_shift_y.setGeometry(15, 46, 22, g.height())
        f.slider_shift_y.setValue(50)
        def yshift_change(*args, **kwargs):
            # canvas.axes.set
            print(f.slider_shift_y.value())
        f.slider_shift_y.sliderReleased.connect(yshift_change)

        f.slider_zoom_x = QtWidgets.QSlider(QtCore.Qt.Horizontal, f)
        f.slider_zoom_x.setSizePolicy(expand, expand)
        f.slider_zoom_x.setGeometry(36, 1, g.width(), 22)
        def xzoom_change(*args, **kwargs):
            print(f.slider_zoom_x.value())

        f.slider_zoom_x.sliderReleased.connect(xzoom_change)
        f.slider_zoom_x.setValue(50)

        f.slider_shift_x = QtWidgets.QSlider(QtCore.Qt.Horizontal, f)
        f.slider_shift_x.setSizePolicy(expand, expand)
        f.slider_shift_x.setGeometry(36, 15, g.width(), 22)
        def xshift_change(*args, **kwargs):
            print(f.slider_shift_x.value())

        f.slider_shift_x.sliderReleased.connect(xshift_change)
        f.slider_shift_x.setValue(50)

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
