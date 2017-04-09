from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager
from IPython.lib import guisupport
from PyQt5.QtWidgets import QDockWidget, QScrollArea, QSizePolicy, QWidget


class ConsoleWidget(QDockWidget):
    def __init__(self, *args, **kwargs):
        super(ConsoleWidget, self).__init__(*args, **kwargs)
        self.console = RichJupyterWidget()
        self.scrollArea = QScrollArea()
        # self.scrollArea.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.console.banner = "Kerem's Super Duper IPython Shell\n"
        self.scrollArea.setWidget(self.console)
        self.console.show()
        self.layout().addWidget(self.scrollArea)

        self.font_size = 6
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

    def push_vars(self, variableDict):
        """
        Given a dictionary containing name / value pairs, push those variables
        to the Jupyter console widget
        """
        self.kernel_manager.kernel.shell.push(variableDict)

    def clear(self):
        """
        Clears the terminal
        """
        self._control.clear()

        # self.kernel_manager

    def print_text(self, text):
        """
        Prints some plain text to the console
        """
        self._append_plain_text(text)

    def execute_command(self, command):
        """
        Execute a command in the frame of the console widget
        """
        self._execute(command, False)