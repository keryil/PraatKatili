import os
import pandas as pd
import numpy as np

from PyQt5.QtWidgets import QMenu, QStyledItemDelegate
from formlayout import QAction, fedit

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
    """
    Short term features:
    1 	Zero Crossing Rate 	The rate of sign-changes of the signal during the duration of a particular frame.
    2 	Energy 	The sum of squares of the signal values, normalized by the respective frame length.
    3 	Entropy of Energy 	The entropy of sub-frames' normalized energies. It can be interpreted as a measure of abrupt changes.
    4 	Spectral Centroid 	The center of gravity of the spectrum.
    5 	Spectral Spread 	The second central moment of the spectrum.
    6 	Spectral Entropy 	Entropy of the normalized spectral energies for a set of sub-frames.
    7 	Spectral Flux 	The squared difference between the normalized magnitudes of the spectra of the two successive frames.
    8 	Spectral Rolloff 	The frequency below which 90% of the magnitude distribution of the spectrum is concentrated.
    9-21 	MFCCs 	Mel Frequency Cepstral Coefficients form a cepstral representation where the frequency bands are not linear but distributed according to the mel-scale.
    22-33 	Chroma Vector 	A 12-element representation of the spectral energy where the bins represent the 12 equal-tempered pitch classes of western-type music (semitone spacing).
    34 	Chroma Deviation 	The standard deviation of the 12 chroma coefficients.
    """
    feat_labels = ["Zero Crossing Rate", "Energy", "Entropy of Energy", "Spectral Centroid", "Spectral Spread", "Spectral Entropy",
                   "Spectral Flux", "Spectral Rolloff"]
    for i in range(13):
        feat_labels.append("MFCC_{}".format(i))
    for i in range(2):
        feat_labels.append("ChromaVector_{}".format(i))
    feat_labels.append("Chroma Deviation")

    datalist = [("Window size", .05),
                ("Step size", .05),
                ("Result alias", "STF")]
    res = fedit(datalist, title="Short term features",
                comment="Returns a matrix that consists of 34 feature time series.")
    if res is not None:
        win_size, step_size, alias = res
        data = audioFeatureExtraction.stFeatureExtraction(data, Fs, win_size * Fs, step_size * Fs)
        series = []
        for row, label in zip(data, feat_labels):
            series.append(pd.Series(data=row, name=label))
        print("{} series produced, of length {}".format(len(series), len(series[0])))
        data = pd.concat(series, axis=1)
        arr = Array(alias=alias, data=data)
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

    def __init__(self, path, alias, *args, **kwargs):
        super(WAVFile, self).__init__(path, *args, alias=alias, **kwargs)
        self.sample_rate = -1

    def open(self):
        self.sample_rate, self.data = audioBasicIO.readAudioFile(self.path)
        self.data = pd.Series(self.data,
                              name="WAV:{}".format(self.alias),
                              dtype=np.float64)
        return self.data

    def __str__(self):
        return "WAVFile({})".format(self.path)


class Array(Resource):
    """
    Resource wrapper for Numpy arrays.
    """
    count = 0

    def __init__(self, alias, data, *args, **kwargs):
        super(Array, self).__init__(alias, *args, **kwargs)
        if not (isinstance(data, pd.DataFrame) or isinstance(data, pd.Series)):
            data = pd.DataFrame(data, dtype=np.float64)
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
