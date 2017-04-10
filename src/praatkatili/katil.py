from PyQt5 import QtGui, QtCore, QtWidgets, uic
from praatkatili.canvas import PlotCanvas
import sys
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
# from matplotlib.figure import Figure
# import matplotlib.pyplot as plt
from qtconsole.inprocess import QtInProcessKernelManager
# from IPython.lib import guisupport
from qtconsole.rich_jupyter_widget import RichJupyterWidget
from PyQt5.QtWidgets import QDockWidget
import os
import resource



main_ui = "res/mainwindow.ui"

class Katil(QtWidgets.QWidget):
    def __init__(self):
        super(Katil, self).__init__()
        self.window = uic.loadUi(main_ui)
        self.window.setCentralWidget(None)
        self.window.show()
        self.console = self.window.findChild(RichJupyterWidget, "console")
        self.console.font_size = 10
        self.plots = []
        self.setup_ipython()

        self.file_model = QtWidgets.QFileSystemModel()
        self.treeview = self.find_children(QtWidgets.QTreeView)

        self.setup_browser()

    def find_docks(self, name=None):
        return self.find_children(QDockWidget, name)

    def find_children(self, type, name=None):
        """
        Finds the children of a certain type, with an optional 
        name. Returns either None, a single child, or a 
        list of children.
        :param type: 
        :param title: 
        :return: 
        """
        # print(type, name)
        # assert isinstance(type, QtWidgets.QWidget)
        ret = self.window.findChildren(type, name)
        try:
            return ret[0]
        except IndexError:
            return ret

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
        print(QtCore.QDir.currentPath())
        self.file_model.setRootPath(QtCore.QDir.currentPath())
        self.treeview.setModel(self.file_model)
        self.treeview.setRootIndex(self.file_model.index(os.getcwd()))

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
        self.push_vars({"_injected":globals()})
        self.execute_command("from PyQt5.QtWidgets import *")

    def inject_debugs(self):
        self.push_vars({'canvas': self.find_children(PlotCanvas)})

if __name__ == "__main__":
    qapp = QtWidgets.QApplication(sys.argv)
    global main_widget
    main_widget = Katil()
    sys.exit(qapp.exec_())