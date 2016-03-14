# -*- coding: utf-8 -*-
import mock
import thclient.client
from jose import jwt
from jose.constants import ALGORITHMS

from releasetasks import make_task_graph as make_task_graph_orig
from releasetasks.test import PUB_KEY, DUMMY_PUBLIC_KEY


def do_common_assertions(graph):
    _cached_taskIDs = set()
    if graph["tasks"]:
        for t in graph["tasks"]:
            task = t["task"]
            assert task["priority"] == "high"
            assert "task_name" in task["extra"]
            assert "signature" in task["extra"].get("signing", {}), \
                "%s is not signed" % task["extra"]["task_name"]
            claims = jwt.decode(task["extra"]["signing"]["signature"],
                                PUB_KEY, algorithms=[ALGORITHMS.RS512])
            assert claims["taskId"] == t["taskId"], \
                "Task ID mismatch in %s signature" % task["extra"]["task_name"]
            properties = task["payload"].get("properties")
            if properties:
                # The following properties are required by log_uploader.py
                # and QE automation
                required_properties = (
                    "version", "build_number", "release_promotion",
                    "revision", "product")
                for prop in required_properties:
                    assert prop in properties
            assert t["taskId"] not in _cached_taskIDs
            assert "routes" in task
            rel_routes = [r.startswith("index.releases.") for r in task["routes"]]
            assert len(rel_routes) >= 2,  "At least 2 release index routes required"
            _cached_taskIDs.add(t["taskId"])


def get_task_by_name(graph, name):
    for t in graph["tasks"]:
        if t["task"]["extra"]["task_name"] == name:
            return t
    return None


@mock.patch.object(thclient.client.TreeherderClient, "get_resultsets")
def make_task_graph(*args, **kwargs):
    args = list(args)
    mocked_get_resultsets = args.pop()
    mocked_get_resultsets.return_value = [{"revision_hash": "abcdefgh1234567"}]
    return make_task_graph_orig(*args, public_key=DUMMY_PUBLIC_KEY,
                                balrog_username="fake", balrog_password="fake",
                                beetmover_aws_access_key_id="baz",
                                beetmover_aws_secret_access_key="norf",
                                running_tests=True, **kwargs)
