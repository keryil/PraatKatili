from PyQt5 import QtGui, QtCore, QtWidgets, uic
from praatkatili.canvas import PlotCanvas
import sys
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from qtconsole.inprocess import QtInProcessKernelManager
from IPython.lib import guisupport
from qtconsole.rich_jupyter_widget import RichJupyterWidget



main_ui = "res/mainwindow.ui"

class Katil(QtWidgets.QWidget):
    def __init__(self):
        super(Katil, self).__init__()
        self.window = uic.loadUi(main_ui)
        # self.canvas = PlotCanvas(self.window, width=5, height=4)
        self.window.show()
        self.console = self.window.findChild(RichJupyterWidget, "console")
        self.setup_ipython()

    def setup_ipython(self):
        self.console.kernel_manager = kernel_manager = QtInProcessKernelManager()
        kernel_manager.start_kernel(show_banner=True)
        kernel_manager.kernel.gui = 'qt'
        self.console.kernel_client = kernel_client = self.console._kernel_manager.client()
        kernel_client.start_channels()

        def stop():
            kernel_client.stop_channels()
            kernel_manager.shutdown_kernel()
            guisupport.get_app_qt().exit()

        self.console.exit_requested.connect(stop)


if __name__ == "__main__":
    qapp = QtWidgets.QApplication(sys.argv)
    win = Katil()
    sys.exit(qapp.exec_())