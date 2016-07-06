# -*- coding: utf-8 -*-
import mock
from jose import jwt
from jose.constants import ALGORITHMS

from releasetasks import make_task_graph as make_task_graph_orig
from releasetasks.test import PUB_KEY, DUMMY_PUBLIC_KEY


def do_common_assertions(graph):
    _cached_taskIDs = set()
    if graph["tasks"]:
        for t in graph["tasks"]:
            task = t["task"]
            task_name = task["metadata"]["name"]
            assert "reruns" in t
            assert task["priority"] == "high"
            assert "task_name" in task["extra"]
            assert "build_props" in task["extra"], "inlcude common_extras.yml.tmpl"
            for prop in ["product", "locales", "branch", "platform", "version",
                         "revision", "build_number"]:
                assert prop in task["extra"]["build_props"]
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
            # encryptedEnvs = task["payload"].get("encryptedEnv")
            # if encryptedEnvs:
            #    for encryptedEnv in encryptedEnvs:
            #        # TODO: Check the encryptedEnv endTime >= task deadline
            #        #    Requires a private key of the dummy pubkey we use.
            #        #    Can use from taskcluster.utils import decryptMessage
            assert t["taskId"] not in _cached_taskIDs
            assert "routes" in task
            rel_routes = [r.startswith("index.releases.") for r in task["routes"]]
            assert len(rel_routes) >= 2, "At least 2 release index routes required"

            if task["provisionerId"] == "buildbot-bridge":
                assert "treeherder" not in task["extra"], \
                    "remove treeherder from {}: {}".format(task_name, task)
                assert "treeherderEnv" not in task["extra"], \
                    "remove treeherderEnv from {}: {}".format(task_name, task)
                assert not any([r.startswith("tc-treeherder") for r in task["routes"]]), \
                    "remove treeherder routes from {}: {}".format(task_name, task)

            if task["provisionerId"] == "aws-provisioner-v1":
                assert "treeherder" in task["extra"], \
                    "add treeherder to {}: {}".format(task_name, task)
                assert "treeherderEnv" in task["extra"], \
                    "add treeherderEnv to {}: {}".format(task_name, task)
                assert len([r for r in task["routes"] if r.startswith("tc-treeherder")]) == 2, \
                    "{} has to have 2 treeherder routes: {}".format(task_name, task)

            _cached_taskIDs.add(t["taskId"])


def get_task_by_name(graph, name):
    for t in graph["tasks"]:
        if t["task"]["extra"]["task_name"] == name:
            return t
    return None


@mock.patch("releasetasks.get_json_rev")
def make_task_graph(*args, **kwargs):
    args = list(args)
    mocked_get_json_rev = args.pop()
    mocked_get_json_rev.return_value = {"pushid": 78123}
    return make_task_graph_orig(*args, public_key=DUMMY_PUBLIC_KEY,
                                balrog_username="fake", balrog_password="fake",
                                beetmover_aws_access_key_id="baz",
                                beetmover_aws_secret_access_key="norf",
                                running_tests=True, **kwargs)
