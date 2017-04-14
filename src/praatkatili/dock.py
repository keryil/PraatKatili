import os

from PyQt5 import QtCore
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QDockWidget, QAbstractItemView
from qtconsole.inprocess import QtInProcessKernelManager
from qtconsole.rich_jupyter_widget import RichJupyterWidget

from praatkatili.canvas import PlotCanvas
from praatkatili.config import *


class Dock(QDockWidget):
    def __init__(self, *args, **kwargs):
        super(Dock, self).__init__(*args, **kwargs)
        self.setFeatures(DOCK_FEATURES)


class FileBrowserDock(Dock):
    def __init__(self, file_model, *args, **kwargs):
        super(FileBrowserDock, self).__init__(*args, **kwargs)
        self.setMinimumWidth(300)
        self.setMinimumHeight(125)
        self.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.setWindowTitle("File Browser")

        self.file_view = view = QtWidgets.QTreeView()
        self.setWidget(self.file_view)

        self.file_model = file_model
        self.file_model.setRootPath(QtCore.QDir.homePath())
        view.setModel(self.file_model)
        view.setRootIndex(self.file_model.index(QtCore.QDir.homePath()))

        view.setAutoScroll(True)
        view.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        view.setAutoExpandDelay(0)
        # view.doubleClicked.connect(self.open_file)
        from PyQt5.QtCore import QTimer
        t = t = QTimer()
        t.singleShot(500, self.show_folder)

    def view_and_model(self):
        return self.file_view, self.file_model

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


class IPythonDock(Dock):
    def __init__(self, *args, **kwargs):
        super(IPythonDock, self).__init__(*args, **kwargs)
        self.setMinimumHeight(80)
        self.setMinimumWidth(500)
        self.setWindowTitle("IPython Shell")
        self.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.console = RichJupyterWidget(name="console")
        self.console.font_size = 7
        self.setWidget(self.console)

    def setup_ipython(self, main_window):
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

        self.console.exit_requested.connect(stop)
        self.push_vars({"KatilInstance": main_window})
        self.console.show()
        self.inject_globals()
        self.inject_debugs()

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

    def inject_globals(self, glbls=None):
        """
        Inject the globals() dict into the IPython kernel
        under the key '_injected'
        :return:
        """
        if glbls is None:
            glbls = globals()
        self.push_vars({"_injected": glbls})
        self.execute_command("from PyQt5.QtWidgets import *")
        self.execute_command("from praatkatili import *")

    def inject_debugs(self):
        self.push_vars({'canvas': self.findChildren(PlotCanvas)})


class PlotDock(Dock):
    yzoom_changed = QtCore.pyqtSignal(int, name="YZoomChanged")
    xzoom_changed = QtCore.pyqtSignal(int, name="XZoomChanged")
    xshift_changed = QtCore.pyqtSignal(int, name="XShiftChanged")
    yshift_changed = QtCore.pyqtSignal(int, name="YShiftChanged")

    def __init__(self, main_window, tab_group, *args, **kwargs):
        super(PlotDock, self).__init__(*args, **kwargs)
        self.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.tab_group = tab_group

        expand = QtWidgets.QSizePolicy.Expanding

        # scroll area in dock window
        sc = QtWidgets.QScrollArea()
        sc.setAlignment(QtCore.Qt.AlignCenter)
        sc.setLayout(QtWidgets.QFormLayout())
        sc.setSizePolicy(expand, expand)
        self.setWidget(sc)

        # frame within scroll area
        self.frame = f = QtWidgets.QWidget()
        f.setLayout(QtWidgets.QFormLayout())
        f.setSizePolicy(expand, expand)

        # canvas on frame
        self.canvas = canvas = PlotCanvas(f)
        canvas.setSizePolicy(expand, expand)
        sc.setWidget(f)
        f.setGeometry(canvas.geometry())
        sc.setGeometry(f.geometry())
        self.setWindowTitle("{} (plot{:>2})".format(canvas.axes.get_title(),
                                                    main_window.plot_counter))

        canvas.dock = self
        self.setup_sliders()

    def setup_slider(self, slider, geometry, signal):
        expand = QtWidgets.QSizePolicy.Expanding
        slider.setSizePolicy(expand, expand)
        slider.setGeometry(geometry)
        slider.setValue(50)

        # connect slider release to a separate signal to avoid
        # redrawing plots for intermittent values
        slider.sliderReleased.connect(
            lambda: signal.emit(slider.value()))

    def setup_sliders(self):
        canvas = self.canvas
        f = self.frame
        g = canvas.geometry()

        f.slider_zoom_y = QtWidgets.QSlider(QtCore.Qt.Vertical, f)
        geo = QtCore.QRect(2, 46, 22, g.height() - 50)
        self.setup_slider(f.slider_zoom_y, geo, self.yzoom_changed)

        f.slider_shift_y = QtWidgets.QSlider(QtCore.Qt.Vertical, f)
        geo.setLeft(15)
        self.setup_slider(f.slider_shift_y, geo, self.yshift_changed)

        f.slider_zoom_x = QtWidgets.QSlider(QtCore.Qt.Horizontal, f)
        geo = QtCore.QRect(36, 1, g.width() - 50, 22)
        self.setup_slider(f.slider_zoom_x, geo, self.xzoom_changed)

        f.slider_shift_x = QtWidgets.QSlider(QtCore.Qt.Horizontal, f)
        geo.setTop(15)
        self.setup_slider(f.slider_shift_x, geo, self.xshift_changed)

class ResourceDock(Dock):
    def __init__(self, *args, **kwargs):
        super(ResourceDock, self).__init__(*args, **kwargs)
        self.setMinimumWidth(300)
        self.setMinimumHeight(125)
        self.setFeatures(DOCK_FEATURES)
        self.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.setWindowTitle("Resources")

        self.resource_view = resource_view = QtWidgets.QTreeView()
        self.resource_model = resource_model = QStandardItemModel()
        resource_model.setColumnCount(4)
        resource_model.setHorizontalHeaderLabels(["Alias",
                                                       "Type",
                                                       "Path",
                                                       "Value"])
        resource_view.setModel(resource_model)

    def view_and_model(self):
        return self.resource_view, self.resource_model

    def add_resource(self, resource):
        r, r2, r3, r4 = QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem()
        r.setText(resource.alias)
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
        self.resource_model.appendRow([r, r2, r3, r4])
