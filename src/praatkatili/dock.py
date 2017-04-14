from PyQt5.QtGui import QStandardItemModel
from PyQt5.QtWidgets import QDockWidget
from PyQt5 import QtWidgets, QtCore
from praatkatili.config import *
from praatkatili.canvas import PlotCanvas


class Dock(QDockWidget):
    def __init__(self, *args, **kwargs):
        super(QDockWidget, self).__init__(*args, **kwargs)


class PlotDock(Dock):
    def __init__(self, main_window, tab_group, *args, **kwargs):
        super(QDockWidget, self).__init__(*args, **kwargs)
        self.setFeatures(DOCK_FEATURES)
        self.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        # dock.setLayout(QtWidgets.QFormLayout())
        self.tab_group = tab_group

        expand = QtWidgets.QSizePolicy.Expanding
        maximum = QtWidgets.QSizePolicy.Maximum

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

    def setup_sliders(self):
        canvas = self.canvas
        f = self.frame
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


class ResourceDock(Dock):
    def __init__(self, *args, **kwargs):
        super(QDockWidget, self).__init__(*args, **kwargs)
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