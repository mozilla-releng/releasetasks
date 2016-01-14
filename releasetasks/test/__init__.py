# -*- coding: utf-8 -*-
import os

import mock
import thclient.client

from releasetasks import make_task_graph as make_task_graph_orig


def read_file(path):
    with open(path) as f:
        return f.read()


def do_common_assertions(graph):
    _cached_taskIDs = set()
    if graph["tasks"]:
        for t in graph["tasks"]:
            task = t["task"]
            assert task["priority"] == "high"
            assert "task_name" in task["extra"]
            assert "signature" in task["extra"].get("signing", {}), \
                "%s is not signed" % task["extra"]["task_name"]
            properties = task["payload"].get("properties")
            if properties:
                # The following properties are required by log_uploader.py
                # and QE automation
                required_properties = (
                    "version", "build_number", "release_promotion",
                    "revision")
                for prop in required_properties:
                    assert prop in properties
            assert t["taskId"] not in _cached_taskIDs
            _cached_taskIDs.add(t["taskId"])


PVT_KEY_FILE = os.path.join(os.path.dirname(__file__), "id_rsa")
PVT_KEY = read_file(PVT_KEY_FILE)
PUB_KEY = read_file(os.path.join(os.path.dirname(__file__), "id_rsa.pub"))
OTHER_PUB_KEY = read_file(os.path.join(os.path.dirname(__file__),
                                       "other_rsa.pub"))
DUMMY_PUBLIC_KEY = os.path.join(os.path.dirname(__file__), "public.key")


def get_task_by_name(graph, name):
    for t in graph["tasks"]:
        if t["task"]["extra"]["task_name"] == name:
            return t
    return None


def get_task_by_slugid(graph, slugid):
    for t in graph["tasks"]:
        if t["taskId"] == slugid:
            return t
    return None


@mock.patch.object(thclient.client.TreeherderClient, "get_resultsets")
def make_task_graph(*args, **kwargs):
    args = list(args)
    mocked_get_resultsets = args.pop()
    mocked_get_resultsets.return_value = [{"revision_hash": "abcdefgh1234567"}]
    return make_task_graph_orig(*args, public_key=DUMMY_PUBLIC_KEY,
                                balrog_username="fake", balrog_password="fake",
                                running_tests=True, **kwargs)
