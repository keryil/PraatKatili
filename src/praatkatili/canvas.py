import randomfrom PyQt5.QtWidgets import QSizePolicyfrom matplotlib import pyplot as pltfrom matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvasfrom matplotlib.figure import Figureplt.style.use("ggplot")class PlotCanvas(FigureCanvas):    """    Matplotlib canvas that holds exactly one figure.     """    def __init__(self, parent=None, width=5, height=4, dpi=100, blank=False):        fig = Figure(figsize=(width, height), dpi=dpi)        self.axes = fig.add_subplot(111)        FigureCanvas.__init__(self, fig)        self.setParent(parent)        FigureCanvas.setSizePolicy(self,                                   QSizePolicy.Expanding,                                   QSizePolicy.Expanding)        self.centre_shift = [0, 0]        self.centre = [0, 0]        self.scale = [1, 1]        FigureCanvas.updateGeometry(self)        self.xlim, self.ylim = self.axes.get_xlim(), self.axes.get_ylim()        # self.called_func = []        # self.called_args = []        self.plot()        if blank:            self.clear()    # def draw(self):    #     super(PlotCanvas, self).draw()    #     self.recenter()    def plot(self):        data = [random.random() * 60 for i in range(25)]        self.axes.plot(data)        self.axes.set_title('PyQt Matplotlib Example')        self.axes.autoscale()        self.recenter()        self.draw()    def clear(self):        self.axes.clear()    def recenter(self):        self.xlim = self.axes.get_xlim()        self.ylim = self.axes.get_ylim()        self.centre[0] = sum(self.xlim) / 2        self.centre[1] = sum(self.ylim) / 2        self.xdelta = abs(self.xlim[1] - self.xlim[0]) / 20.        self.ydelta = abs(self.ylim[1] - self.ylim[0]) / 20.    def set_dock(self, dock):        self.dock = dock    def set_title(self, title):        self.axes.set_title(title)        t = self.dock.windowTitle().split("(")[-1]        self.dock.setWindowTitle("{} ({}".format(title, t))        self.draw()    def plot_line(self, data, title=None):        # self.called_func.append(self.plot_line)        # self.called_args.append((data, title))        self.axes.plot(data)        if title is not None:            self.set_title(title)        self.recenter()        self.draw()    def plot_scatter(self, data, title=None):        # self.called_func.append(self.plot_line)        # self.called_args.append((data, title))        self.axes.scatter(*zip(*enumerate(data)))        if title is not None:            self.set_title(title)        self.recenter()        self.draw()    def reset(self):        self.axes.autoscale()    def set_xshift(self, n):        self.centre_shift[0] = n        self.draw()    def set_yshift(self, n):        self.centre_shift[1] = n        self.draw()    def set_xzoom(self, n):        # scale between 0, 1000        self.scale[0] = 5 - (n + 250) / 500 * 5        # if n < 0:        #     self.scale[0] *= -1        self.draw()    def set_yzoom(self, n):        self.scale[1] = 5 - (n + 250) / 500 * 5        self.draw()    def draw(self):        radius_x = (self.xlim[1] - self.xlim[0]) / 2        radius_y = (self.ylim[1] - self.ylim[0]) / 2        new_xlim = self.xdelta * self.centre_shift[0] + self.centre[0]        new_xlim += (-radius_x * self.scale[0], radius_x * self.scale[0])        new_ylim = self.ydelta * self.centre_shift[1] + self.centre[1]        new_ylim += (-radius_y * self.scale[1], radius_y * self.scale[1])        self.axes.set_xlim(*new_xlim)        self.axes.set_ylim(*new_ylim)        super(PlotCanvas, self).draw()