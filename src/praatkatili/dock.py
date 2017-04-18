import locale
import os
import shlex
import subprocess

import jupyter_core

encoding = locale.getdefaultlocale()[1]

from PyQt5 import QtCore, QtWebEngineWidgets
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QDockWidget, QAbstractItemView, QLabel, QTabWidget
from qtconsole.inprocess import QtInProcessKernelManager
from qtconsole.rich_jupyter_widget import RichJupyterWidget

from praatkatili.canvas import PlotCanvas
from praatkatili.config import *
from praatkatili.util import sanitize_alias


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
        # view.doubleClicked.connect(self.add_file_resource)
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
        self.setMinimumHeight(25)
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

    def pull_var(self, varName, delete=False):
        v = self.console.kernel_manager.kernel.shell.user_ns[varName]
        if delete:
            del self.console.kernel_manager.kernel.shell.user_ns[varName]
        return v

    def delete_var(self, varName):
        del self.console.kernel_manager.kernel.shell.user_ns[varName]

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


    def __init__(self, main_window, tab_group, blank, *args, **kwargs):
        super(PlotDock, self).__init__(*args, **kwargs)
        self.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.tab_group = tab_group

        self.pan_step_size = 10

        expand = QtWidgets.QSizePolicy.Expanding

        # scroll area in dock window
        sc = QtWidgets.QScrollArea()
        sc.setAlignment(QtCore.Qt.AlignCenter)
        sc.setLayout(QtWidgets.QHBoxLayout())
        sc.setSizePolicy(expand, expand)
        self.setWidget(sc)

        # frame within scroll area
        self.frame = f = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout()
        layout.setSpacing(10)
        # layout.setContentsMargins(50,50,50,50)
        f.setLayout(layout)
        f.setSizePolicy(expand, expand)

        # canvas on frame
        self.canvas = canvas = PlotCanvas(blank=blank, dock=self)
        f.layout().addWidget(canvas, 2, 2, 1, 3)
        canvas.setSizePolicy(expand, expand)
        sc.setWidget(f)
        f.setGeometry(canvas.geometry())
        sc.setGeometry(f.geometry())
        self.setWindowTitle("{} (plot{:>2})".format(canvas.axes.get_title(),
                                                    main_window.plot_counter))

        self.setup_sliders()

    def setup_slider(self, slider, geometry, signal):
        expand = QtWidgets.QSizePolicy.Expanding
        slider.setSizePolicy(expand, expand)
        slider.setGeometry(geometry)
        slider.setValue(0)
        slider.setMinimum(-250)
        slider.setMaximum(250)

        # optional: connect slider release to a separate signal to avoid
        # redrawing plots for intermittent values
        slider.valueChanged.connect(
            lambda: signal.emit(slider.value()))

    def setup_sliders(self):
        canvas = self.canvas
        f = self.frame
        g = canvas.geometry()
        l = f.layout()

        f.slider_zoom_y = QtWidgets.QSlider(QtCore.Qt.Vertical, f)
        geo = QtCore.QRect(2, 46, 22, g.height() - 50)
        self.setup_slider(f.slider_zoom_y, geo, self.yzoom_changed)
        l.addWidget(QLabel("Zoom"), 0, 0, 1, 1)
        l.addWidget(f.slider_zoom_y, 1, 0, 3, 1)

        f.slider_shift_y = QtWidgets.QSlider(QtCore.Qt.Vertical, f)
        # geo.setLeft(15)
        self.setup_slider(f.slider_shift_y, geo, self.yshift_changed)
        l.addWidget(QLabel("Pan"), 0, 1, 1, 1)
        l.addWidget(f.slider_shift_y, 1, 1, 3, 1)

        f.slider_zoom_x = QtWidgets.QSlider(QtCore.Qt.Horizontal, f)
        geo = QtCore.QRect(36, 1, g.width() - 50, 22)
        self.setup_slider(f.slider_zoom_x, geo, self.xzoom_changed)
        l.addWidget(QLabel("Zoom"), 0, 2, 1, 1)
        l.addWidget(f.slider_zoom_x, 0, 3,
                    1, 2)

        f.slider_shift_x = QtWidgets.QSlider(QtCore.Qt.Horizontal, f)
        # geo.setTop(15)
        self.setup_slider(f.slider_shift_x, geo, self.xshift_changed)
        l.addWidget(QLabel("Pan"), 1, 2, 1, 1)
        l.addWidget(f.slider_shift_x, 1, 3,
                    1, 2)

        l.setColumnMinimumWidth(2, 22)
        l.setSpacing(5)


class ResourceDock(Dock):
    def __init__(self, main_window, *args, **kwargs):
        super(ResourceDock, self).__init__(*args, **kwargs)
        self.setMinimumWidth(300)
        self.setMinimumHeight(125)
        self.setFeatures(DOCK_FEATURES)
        self.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.setWindowTitle("Resources")
        self.main_window = main_window
        print(self.contextMenuPolicy())

        self.resource_view = resource_view = QtWidgets.QTreeView()
        self.resource_model = resource_model = QStandardItemModel()
        resource_model.setColumnCount(4)
        resource_model.setHorizontalHeaderLabels(["Alias",
                                                  "Type",
                                                  "Path",
                                                  "Value"])
        resource_view.setModel(resource_model)
        resource_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        resource_view.customContextMenuRequested.connect(self.context_menu)
        resource_view.doubleClicked.connect(self.display_resource)

        # actions

    # def setup_actions(self):
    #     self.plot_line = QAc
    def display_resource(self):
        selected = self.resource_view.currentIndex()
        item = self.resource_model.itemFromIndex(selected)
        self.main_window.consoleDock.execute_command(sanitize_alias(item.data().alias) + ".data")

    def context_menu(self, point):
        # find the selected resource
        selected = self.resource_view.currentIndex()
        item = self.resource_model.itemFromIndex(selected)
        if item is None:
            return
        menu = item.data().create_context_menu(self, self.main_window)
        menu.exec_(self.mapToGlobal(point))

    def view_and_model(self):
        return self.resource_view, self.resource_model

    def add_resource(self, resource):
        cname = resource.__class__.__name__
        r1, r2, r3, r4 = QStandardItem(), QStandardItem(), QStandardItem(), QStandardItem()
        r1.setText(resource.alias)
        r2.setText(cname)
        r2.setEditable(False)
        try:
            r3.setText(resource.path)
        except AttributeError:
            r3.setText("N/A")
        r3.setEditable(False)
        r4.setText(str(resource).strip())
        r4.setEditable(False)
        for r in (r1, r2, r3, r4):
            r.setData(resource)
        self.resource_model.appendRow([r1, r2, r3, r4])

        # choose the appropriate item delegate
        from praatkatili.resources import Delegates
        if cname in Delegates:
            print("Custom delegate for row {}: {}".format(self.resource_model.rowCount(),
                                                          Delegates[cname]))
            self.resource_view.setItemDelegateForRow(self.resource_model.rowCount(),
                                                     Delegates[cname])

    def delete_resource(self, resource):
        found = self.main_window.resource_model.findItems(resource.data().alias)[0]
        self.main_window.resource_model.removeRow(found.row())
        print()


class NotebookTab(QtWebEngineWidgets.QWebEngineView):
    def __init__(self, dock, *args, **kwargs):
        super(NotebookTab, self).__init__(*args, **kwargs)
        self.dock = dock
        self.titleChanged.connect(self.refresh_title)

    # def load(self, url):
    #     super(NotebookTab, self).load(url)
    #     self.refresh_title()

    def refresh_title(self, title=None):
        if title is None:
            title = self.title()
        self.dock.tabWidget.setTabText(self.dock.tabWidget.indexOf(self),
                                       title)

    # def showEvent(self, event):
    #     super(NotebookTab, self).showEvent(event)
    #     self.refresh_title()


    def createWindow(self, QWebEnginePage_WebWindowType):
        tab = self.dock.addTab()
        self.dock.tabWidget.setCurrentWidget(tab)
        return tab


class NotebookDock(Dock):
    def __init__(self, main_window, *args, **kwargs):
        super(NotebookDock, self).__init__(*args, **kwargs)
        self.tabWidget = QTabWidget()
        self.main_window = main_window
        self.jupyter_process = None
        self.connection_json = None

        expand = QtWidgets.QSizePolicy.Expanding
        f = QtWidgets.QFrame()
        f.setLayout(QtWidgets.QHBoxLayout())
        f.setSizePolicy(expand, expand)
        self.setWidget(f)
        f.layout().addWidget(self.tabWidget)
        self.setWindowTitle("IPython Notebooks")
        self.start_server()
        self.addTab()
        # self.browser.show()
        # self.load()

    def addTab(self, url=None, request=None):
        tab = NotebookTab(dock=self)
        if request is not None:
            request.openIn(tab)
        if url is None:
            tab.load(self.url)
        self.tabWidget.addTab(tab, "")
        return tab

    def closeEvent(self, event):
        self.stop_server()
        super(NotebookDock, self).closeEvent(event)

    def start_server(self):
        from glob import glob
        if self.jupyter_process is not None:
            self.stop_server()
        json_dir = jupyter_core.paths.jupyter_runtime_dir()
        jsons_before = glob(os.path.join(json_dir, "*.json"))
        args = shlex.split("jupyter notebook --no-browser")
        self.jupyter_process = p = subprocess.Popen(args=args,
                                                    stderr=subprocess.PIPE)

        # figure out the url from the initial console messages
        line = p.stderr.readline().decode(encoding).strip()
        while "localhost" not in line:
            line = p.stderr.readline().decode(encoding).strip()
        self.url = QtCore.QUrl(line.split("at: ")[-1])
        from time import sleep;
        sleep(.5)
        jsons_after = glob(os.path.join(json_dir, "*.json"))
        for json in jsons_after:
            if json not in jsons_before:
                self.connection_json = json
                break
        else:
            raise FileNotFoundError("Could not find the connection JSON in {}.".format(json_dir))

    def stop_server(self):
        if self.jupyter_process:
            print("Killing Jupyter process (PID {})...".format(self.jupyter_process.pid))
            self.jupyter_process.kill()
            outs, errs = self.jupyter_process.communicate()
            self.jupyter_process = None
            self.connection_json = None

    def __del__(self):
        self.stop_server()
