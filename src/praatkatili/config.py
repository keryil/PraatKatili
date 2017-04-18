"""
This is the global configuration module.
"""

from PyQt5 import QtWidgets

DOCK_FEATURES = QtWidgets.QDockWidget.AllDockWidgetFeatures
DOCK_OPTIONS = (QtWidgets.QMainWindow.AllowNestedDocks | QtWidgets.QMainWindow.AllowTabbedDocks | \
                QtWidgets.QMainWindow.AnimatedDocks) & ~QtWidgets.QMainWindow.ForceTabbedDocks
