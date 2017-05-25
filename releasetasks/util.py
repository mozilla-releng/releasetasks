import time
import requests
from jose import jws
from jose.constants import ALGORITHMS
from redo import retriable


ftp_platform_map = {
    'win32': 'win32',
    'win64': 'win64',
    'linux': 'linux-i686',
    'linux64': 'linux-x86_64',
    'macosx64': 'mac'
}

bouncer_platform_map = {
    'win32': 'win',
    'win64': 'win64',
    'linux': 'linux',
    'linux64': 'linux64',
    'macosx64': 'osx'
}

workertype_map = {
    'win32': 'gecko-3-b-linux',
    'win64': 'gecko-3-b-linux',
    'linux': 'gecko-3-b-linux',
    'linux64': 'gecko-3-b-linux',
    'macosx64': 'os-x-10-10-gw'
}

provisionerid_map = {
    'win32': 'aws-provisioner-v1',
    'win64': 'aws-provisioner-v1',
    'linux': 'aws-provisioner-v1',
    'linux64': 'aws-provisioner-v1',
    'macosx64': 'scl3-puppet'
}

DEFAULT_WORKER_TYPE = 'gecko-3-b-linux'
DEFAULT_PROVISIONER_ID = 'aws-provisioner-v1'


def treeherder_platform(platform):
    # See https://github.com/mozilla/treeherder/blob/master/ui/js/values.js
    m = {
        "linux": "linux32",
        "linux64": "linux64",
        "macosx64": "osx-10-10",
        "win32": "windowsxp",
        "win64": "windows8-64",
        "android-4-2-x86": "android-x86",
        "android-4-0-armv7-api15": "android"
    }
    return m[platform]


def sign_task(task_id, pvt_key, valid_for=3600, algorithm=ALGORITHMS.RS512):
    # reserved JWT claims, to be verified
    # Issued At
    iat = int(time.time())
    # Expiration Time
    exp = iat + valid_for
    claims = {
        "iat": iat,
        "exp": exp,
        "taskId": task_id,
        "version": "1",
    }
    return jws.sign(claims, pvt_key, algorithm=algorithm)


def buildbot2ftp(platform):
    return ftp_platform_map.get(platform, platform)


def buildbot2bouncer(platform):
    return bouncer_platform_map.get(platform, platform)


def get_worker_type(platform):
    return workertype_map.get(platform, DEFAULT_WORKER_TYPE)


def get_provisionerid(platform):
    return provisionerid_map.get(platform, DEFAULT_PROVISIONER_ID)


@retriable(sleeptime=0, jitter=0, retry_exceptions=(requests.HTTPError,))
def get_json_rev(repo_path, revision):
    url = "https://hg.mozilla.org/{repo_path}/json-rev/{revision}".format(
        repo_path=repo_path, revision=revision)
    req = requests.get(url, timeout=20)
    req.raise_for_status()
    return req.json()
