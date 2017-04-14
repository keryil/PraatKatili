import random

from PyQt5.QtWidgets import QSizePolicy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class PlotCanvas(FigureCanvas):
    """
    Matplotlib canvas that holds exactly one figure. 
    """
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)

        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        self.centre_shift = [0, 0]
        self.centre = [0, 0]
        self.scale = [250, 250]

        FigureCanvas.updateGeometry(self)
        self.xlim, self.ylim = self.axes.get_xlim(), self.axes.get_ylim()
        self.scaled_xlim, self.scaled_ylim = self.xlim, self.ylim
        self.xdelta = abs(self.xlim[1] - self.xlim[0]) / 50.
        self.ydelta = abs(self.ylim[1] - self.ylim[0]) / 50.
        self.defaults = (self.xlim, self.ylim)
        self.plot()

    # def draw(self):
    #     super(PlotCanvas, self).draw()
    #     self.recenter()

    def plot(self):
        data = [random.random() for i in range(25)]
        self.axes.plot(data, 'r-')
        self.axes.set_title('PyQt Matplotlib Example')
        self.recenter()
        self.draw()

    def recenter(self):
        self.centre[0] = sum(self.axes.get_xlim()) / 2
        self.centre[1] = sum(self.axes.get_ylim()) / 2

    def set_dock(self, dock):
        self.dock = dock

    def set_title(self, title):
        self.axes.set_title(title)
        t = self.dock.windowTitle().split("(")[-1]
        self.dock.setWindowTitle("{} ({}".format(title, t))
        self.draw()

    def plot_line(self, data, title=None):
        self.axes.plot(data, 'r-')
        if title is not None:
            self.set_title(title)
        self.recenter()
        self.draw()

    def reset(self):
        self.axes.autoscale()

    def set_xshift(self, n):
        self.centre_shift[0] = n
        self.draw()

    def set_yshift(self, n):
        self.centre_shift[1] = n
        self.draw()

    def set_xzoom(self, n):
        self.scale[0] = 250 + n
        self.draw()

    def set_yzoom(self, n):
        self.scale[1] = 250 + n
        self.draw()

    def draw(self):
        new_xlim = self.xdelta * self.centre_shift[0] + self.centre[0]
        new_xlim += (-self.xdelta * self.scale[0], self.xdelta * self.scale[0])
        new_ylim = self.ydelta * self.centre_shift[1] + self.centre[1]
        new_ylim += (-self.ydelta * self.scale[1], self.ydelta * self.scale[1])
        self.axes.set_xlim(*new_xlim)
        self.axes.set_ylim(*new_ylim)
        super(PlotCanvas, self).draw()

    # def move_horizontally(self, n=1):
    #     self.axes.set_xlim(*(self.xlim+self.xdelta * n))
    #     # self.recenter()
    #     self.draw()
    #
    # def move_vertically(self, n=1):
    #     self.axes.set_ylim(*(self.ylim() + self.ydelta * n))
    #     # self.recenter()
    #     self.draw()

    def zoom_horizontally(self, n=1):
        x1, x2 = self.axes.get_xlim()
        # n = n ** 2
        # if n > 0:
        #     self.axes.set_xlim(x1 + self.xdelta * n, x2 - self.xdelta * n)
        # else:
        new_lims = x1 - self.xdelta * n, x2 + self.xdelta * n
        self.axes.set_xlim(new_lims + self.centre[0])
        # self.scaled_xlim = self.axes.get_xlim()
        self.draw()

    def zoom_vertically(self, n=1):
        y1, y2 = self.axes.get_ylim()
        # n = n ** 2
        # if n > 0:
        #     self.axes.set_ylim(y1 + self.ydelta * n, y2 - self.ydelta * n)
        # else
        new_lims = y1 - self.ydelta * n, y2 + self.ydelta * n
        self.axes.set_ylim(new_lims + self.centre[1])
        # self.scaled_ylim = self.axes.get_ylim()
        self.draw()
