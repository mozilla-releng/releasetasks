import time
import requests
from jose import jws
from jose.constants import ALGORITHMS
from redo import retriable
from collections import OrderedDict
from copy import deepcopy
from toposort import toposort_flatten
from taskcluster.utils import slugId

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


@retriable(sleeptime=0, jitter=0, retry_exceptions=(requests.HTTPError,))
def get_json_rev(repo_path, revision):
    url = "https://hg.mozilla.org/{repo_path}/json-rev/{revision}".format(
        repo_path=repo_path, revision=revision)
    req = requests.get(url, timeout=20)
    req.raise_for_status()
    return req.json()


def graph_to_tasks(graph):
    """Convert a graph into a list of tasks.
    Replaces graph level "requires" into task-level "dependencies"
    """
    tasks = OrderedDict()
    for t in graph["tasks"]:
        # If a task doesn't have any dependencies it will be scheduled even if
        # the whole submission fails. To make the submission atomic, we create
        # a dummy task, which is resolved at the end of the submission to
        # unblock the scheduling
        task = t["task"]
        # `requires` is `dependencies` in queue
        if t.get("requires"):
            task["dependencies"] = t["requires"]
        # Poor man's replacement of taskgraph's `reruns`. Docker worker suports
        # retrying on specific exit statuses. Using exit code 1 by default.
        if task["provisionerId"] == "aws-provisioner-v1":
            task["payload"]["onExitStatus"] = task["payload"].get("onExitStatus") or \
                {'retry': [1]}

        tasks[t["taskId"]] = task

    return tasks


def add_atomic_task(tasks, toplevel_task):
    """Adds top level task to be resolved after successful submission"""
    tasks = deepcopy(tasks)
    tl_task_id, toplevel_task_def = toplevel_task
    for t in tasks.itervalues():
        if "dependencies" not in t:
            t["dependencies"] = [tl_task_id]
    tasks[tl_task_id] = toplevel_task_def
    return tasks


def sort_tasks(tasks):
    to_sort = {task_id: set(task.get("dependencies", []))
               for task_id, task in tasks.iteritems()}
    ordered = toposort_flatten(to_sort)
    return OrderedDict(
        sorted(tasks.items(), key=lambda t: ordered.index(t[0]))
    )


def inject_dummy_tasks(tasks, dummy_task, max_deps=100):
    # The current TC Queue implementation doesn't let one specify more than 100
    # dependencies. To work around this issue we need to ddd dummy tasks and
    # change the original "dependencies" value.
    new_tasks = OrderedDict()
    for task_id, task in tasks.iteritems():
        task = deepcopy(task)
        deps = task.get("dependencies", [])
        if len(deps) > max_deps:
            num_dummy_tasks = int(round(len(deps)/float(max_deps) + 0.5))
            dummy_tasks = OrderedDict()
            for i in range(num_dummy_tasks):
                cur_deps = deps[i * max_deps:(i + 1) * max_deps]
                curr_dummy_task = deepcopy(dummy_task)
                curr_dummy_task["dependencies"] = cur_deps
                dummy_tasks[slugId()] = curr_dummy_task
            task["dependencies"] = dummy_tasks.keys()
            new_tasks.update(dummy_tasks)

        new_tasks[task_id] = task

    return new_tasks


def inject_taskGroupId(tasks, taskGroupId):
    new_tasks = OrderedDict()
    for task_id, task in tasks.iteritems():
        task = deepcopy(task)
        task["taskGroupId"] = taskGroupId
        new_tasks[task_id] = task
    return new_tasks
