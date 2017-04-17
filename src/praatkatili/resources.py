import os

from PyQt5.QtWidgets import QMenu, QStyledItemDelegate

from praatkatili.audio_processing import generate_actions
from pyAudioAnalysis import audioBasicIO

# holds all open resource instances
# {resource_class_name: [instance1, instance2, ...]}
OpenResources = dict()

class Resource(object):
    """
    Abstract parent class of all resources such as data from CSV, WAV and such files, as well as 
    other data objects such as pandas frames.
    """
    def __init__(self, alias, *args, **kwargs):
        super(Resource, self).__init__(*args, **kwargs)
        self.alias = alias
        cname = self.__class__.__name__
        if cname not in OpenResources:
            OpenResources[cname] = set()
        OpenResources[cname].add(self)


    def __str__(self):
        return "{}({})".format(self.__class__.__name__, self.alias)

    def open(self):
        raise NotImplementedError()

    def write(self):
        raise NotImplementedError()

    def view(self):
        raise NotImplementedError()

    def plot(self):
        raise NotImplementedError()

    def __del__(self):
        OpenResources.remove(self)

    def __str__(self):
        return str(self.data)

    def create_context_menu(self, parent, main_window):
        menu = QMenu(parent)
        plot_menu = menu.addMenu("Plot")
        plot_menu.addActions(parent.parent().plot_actions)
        process_menu = menu.addMenu("Analysis")
        process_menu.addActions(generate_actions(parent, self, main_window))
        return menu


class FileResource(Resource):
    """
    Generic text file, parent class to all other file resources. 
    """
    file_masks = []

    def __init__(self, path, *args, alias=None, writable=True, **kwargs):
        super(FileResource, self).__init__(alias, *args, **kwargs)
        if not os.path.exists(path):
            raise FileNotFoundError("Invalid path for file resource: {}".format(path))
        self.path = path
        self.writable = writable
        self.data = None

    def __str__(self):
        return "{} ({})".format(super(FileResource, self).__str__(), self.path)

    def open(self):
        self.data = open(self.path, mode="rw" if self.writable else "r")


class CSVFile(FileResource):
    file_masks = ("*.csv",)

    def __init__(self, *args, **kwargs):
        super(CSVFile, self).__init__(*args, **kwargs)


class WAVFile(FileResource):
    """
    Audio file in wave format.  
    """
    file_masks = ("*.wav", "*.wave")

    def __init__(self, path, *args, **kwargs):
        super(WAVFile, self).__init__(path, *args, **kwargs)
        self.sample_rate = -1

    def open(self):
        self.sample_rate, self.data = audioBasicIO.readAudioFile(self.path)
        return self.data


class Array(Resource):
    """
    Resource wrapper for Numpy arrays.
    """
    count = 0

    def __init__(self, alias, data, *args, **kwargs):
        super(Array, self).__init__(alias, *args, **kwargs)
        self.data = data
        self.sample_rate = None

    def open(self):
        pass

    def __str__(self):
        s = "{}({})".format(self.data.__class__.__name__, self.data.shape)
        return s


class ArrayDelegate(QStyledItemDelegate):
    def __init__(self, *args, **kwargs):
        super(ArrayDelegate, self).__init__(*args, **kwargs)


class UnknownResourceTypeError(Exception):
    pass


class DuplicateFileResourceError(Exception):
    pass

FileTypes = {}
for type in (WAVFile, CSVFile):
    for ext in type.file_masks:
        FileTypes[ext] = type

Delegates = {Array: ArrayDelegate}
