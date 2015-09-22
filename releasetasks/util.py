import os
from taskcluster.utils import encryptEnvVar


def treeherder_platform(platform):
    # See https://github.com/mozilla/treeherder/blob/master/ui/js/values.js
    m = {
        "linux": "linux32",
        "linux64": "linux64",
        "macosx64": "osx-10-10",
        "win32": "windowsxp",
        "win64": "windows8-64",
    }
    return m[platform]


def encryptEnvVar_wrapper(*args, **kwargs):
    """Wrap encryptEnvVar and pass key file path"""
    return encryptEnvVar(
        *args, keyFile=os.path.join(os.path.dirname(__file__),
                                    "data", "docker-worker-pub.pem"),
        **kwargs)
