from PyQt5.QtWidgets import QAction
from formlayout import fedit

from praatkatili.resources import Array, FileResource
from pyAudioAnalysis import audioFeatureExtraction

global main_widget



def transform_array(resource, main_win):
    datalist = [("Alias for result", "{}_transformed".format(resource.alias)),
                ("Code to run", "_data + 1")]
    res = fedit(datalist, title="Transform array",
                comment="Applies arbitrary ipython statements to data. Use _data to access the data structure.")
    if res is not None:
        alias, code = res
        main_win.consoleDock.push_vars({"_data": resource.data})
        main_win.consoleDock.execute_command(code + ";")
        data = main_win.consoleDock.pull_var("_data", delete=True)
        arr = resources.Array(alias=alias, data=data)

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
        arr = Array(alias=alias,
                              data=audioFeatureExtraction.stFeatureExtraction(data, Fs, win_size * Fs, step_size * Fs));
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
