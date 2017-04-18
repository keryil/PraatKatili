import os

from PyQt5.QtWidgets import QMenu, QStyledItemDelegate
from formlayout import QAction, fedit

# from praatkatili.audio_processing import generate_actions
from pyAudioAnalysis import audioBasicIO, audioFeatureExtraction


"""
These are actions on resources, as represented in the context menus
"""

def transform_array(resource, main_win):
    datalist = [("Alias for result", "{}_transformed".format(resource.alias)),
                ("Code to run", "_data + 1\n")]
    res = fedit(datalist, title="Transform array",
                comment="Applies arbitrary ipython statements to data. Use _data to access the data structure.")
    if res is not None:
        alias, code = res
        main_win.consoleDock.push_vars({"_data": resource.data})
        main_win.consoleDock.execute_command(code + ";")
        data = main_win.consoleDock.pull_var("_data", delete=True)
        arr = Array(alias=alias, data=data)

        # copy sample rate if it applies
        if hasattr(resource, "sample_rate"):
            arr.sample_rate = resource.sample_rate
        main_win._add_resource(arr)

        return arr


def short_term_features(data, Fs, main_win):
    datalist = [("Window size", .05),
                ("Step size", .05),
                ("Result alias", "STF")]
    res = fedit(datalist, title="Short term features",
                comment="Returns a matrix that consists of 34 feature time series.")
    if res is not None:
        win_size, step_size, alias = res
        arr = Array(alias=alias, data=audioFeatureExtraction.stFeatureExtraction(data, Fs, win_size * Fs, step_size * Fs));
        main_win._add_resource(arr)
        return arr


def generate_actions(parent, resource, main_window):
    to_return = []
    is_numeric = False
    for r in (Array, FileResource):
        if isinstance(resource, r):
            is_numeric = True
            break

    if is_numeric:
        # short term features
        stFeatures = QAction("Short term features...", parent)
        stFeatures.triggered.connect(lambda checked, res=resource:
                                     short_term_features(res.data, res.sample_rate,
                                                         main_window))
        to_return.append(stFeatures)

        # arbitrary transform
        transform = QAction("Arbitrary transform...", parent)
        transform.triggered.connect(lambda checked, res=resource:
                                    transform_array(resource, main_window))
        to_return.append(transform)
    # if isinstance(resource, resources.FileResource)
    return to_return

"""
End of actions
"""

class Resource(object):
    """
    Abstract parent class of all resources such as data from CSV, WAV and such files, as well as 
    other data objects such as pandas frames.
    """
    def __init__(self, alias, *args, **kwargs):
        super(Resource, self).__init__(*args, **kwargs)
        self.alias = alias

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

    def __str__(self):
        return str(self.data)

    def create_context_menu(self, parent, main_window):
        menu = QMenu(parent)
        plot_menu = menu.addMenu("Plot")
        plot_menu.addActions(parent.parent().plot_actions)
        process_menu = menu.addMenu("Analysis")
        process_menu.addActions(generate_actions(parent, self, main_window))
        delete = QAction("Delete", parent)
        selected = main_window.resource_view.currentIndex()
        item = main_window.resource_model.itemFromIndex(selected)
        delete.triggered.connect(lambda checked, res=item:
                                 main_window._delete_resource(res))
        menu.addAction(delete)
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
