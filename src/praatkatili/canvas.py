import randomfrom PyQt5.QtWidgets import QSizePolicyfrom matplotlib import pyplot as pltfrom matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvasfrom matplotlib.figure import Figureplt.style.use("ggplot")class PlotCanvas(FigureCanvas):    """    Matplotlib canvas that holds exactly one figure.     """    def __init__(self, parent=None, width=5, height=4, dpi=100, blank=False,                 dock=None):        fig = Figure(figsize=(width, height), dpi=dpi)        self.axes = fig.add_subplot(111)        self.plot_type = None        self.data = None        self.plot_args = None        self.dock = dock        FigureCanvas.__init__(self, fig)        self.setParent(parent)        FigureCanvas.setSizePolicy(self,                                   QSizePolicy.Expanding,                                   QSizePolicy.Expanding)        self.centre_shift = [0, 0]        self.centre = [0, 0]        self.scale = [1, 1]        FigureCanvas.updateGeometry(self)        self.xlim, self.ylim = self.axes.get_xlim(), self.axes.get_ylim()        # self.called_func = []        # self.called_args = []        self.plot_dummy()        if blank:            self.clear()    def plot_dummy(self):        data = [random.random() * 60 for i in range(25)]        self.plot_line(data, 'Dummy')    def clear(self):        self.axes.clear()    def recenter(self):        self.xlim = self.axes.get_xlim()        self.ylim = self.axes.get_ylim()        self.centre[0] = sum(self.xlim) / 2        self.centre[1] = sum(self.ylim) / 2        self.xdelta = abs(self.xlim[1] - self.xlim[0]) / 20.        self.ydelta = abs(self.ylim[1] - self.ylim[0]) / 20.    def set_dock(self, dock):        self.dock = dock    def set_title(self, title, draw=True):        self.axes.set_title(title)        t = self.dock.windowTitle().split("(")[-1]        self.dock.setWindowTitle("{} ({}".format(title, t))        self.draw() if draw else 1    def get_title(self):        return self.axes.get_title()    def plot_line(self, data=None, title=None):        if data is not None:            self.data = data        self.plot_args = (list(self.data), title)        self.axes.plot(self.data)        if title is not None:            self.set_title(title, draw=False)        self.recenter()        self.plot_type = "line"        self.draw()    def plot_scatter(self, data, title=None):        if data is not None:            self.data = data        self.plot_args = (list(self.data), title)        self.axes.scatter(*zip(*enumerate(self.data)))        if title is not None:            self.set_title(title, draw=False)        self.recenter()        self.plot_type = "scatter"        self.draw()    def reset(self):        self.axes.autoscale()    def set_xshift(self, n):        self.centre_shift[0] = n        self.draw()    def set_yshift(self, n):        self.centre_shift[1] = n        self.draw()    def set_xzoom(self, n):        # scale between 0, 1000        self.scale[0] = 5 - (n + 250) / 500 * 5        # if n < 0:        #     self.scale[0] *= -1        self.draw()    def set_yzoom(self, n):        self.scale[1] = 5 - (n + 250) / 500 * 5        self.draw()    def draw(self):        radius_x = (self.xlim[1] - self.xlim[0]) / 2        radius_y = (self.ylim[1] - self.ylim[0]) / 2        new_xlim = self.xdelta * self.centre_shift[0] + self.centre[0]        new_xlim += (-radius_x * self.scale[0], radius_x * self.scale[0])        new_ylim = self.ydelta * self.centre_shift[1] + self.centre[1]        new_ylim += (-radius_y * self.scale[1], radius_y * self.scale[1])        self.axes.set_xlim(*new_xlim)        self.axes.set_ylim(*new_ylim)        super(PlotCanvas, self).draw()    def to_dict(self):        return {            "plot_args": self.plot_args,            "plot_type": self.plot_type,            "xlim": self.xlim,            "ylim": self.ylim,            "centre_shift": self.centre_shift,            "scale": self.scale,            "title": self.get_title()        }    def from_dict(self, d):        class DictAsObject(object):            def __init__(self, d):                self.__dict__.update(d)        d = DictAsObject(d)        self.clear()        plot_func = "plot_{}".format(d.plot_type)        plot_func = getattr(self, plot_func)        plot_func(*d.plot_args)        self.set_title(d.title, draw=False)        self.axes.set_xlim(d.xlim)        self.axes.set_ylim(d.ylim)        self.centre_shift = d.centre_shift        self.scale = d.scale        self.recenter()        self.draw()