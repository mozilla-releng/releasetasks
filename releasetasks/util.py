import time
from jose import jws
from jose.constants import ALGORITHMS

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
