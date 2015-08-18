# -*- coding: utf-8 -*-
import unittest

from releasetasks import make_task_graph as make_task_graph_orig


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


def make_task_graph(*args, **kwargs):
    return make_task_graph_orig(*args, running_tests=True, **kwargs)


class TestMakeTaskGraph(unittest.TestCase):
    """Because of huge the graph gets, verifying every character of it is
    impossible to maintain. Instead, we verify aspects of it. Eg, making sure
    the correct number of funsize partials are happening, rather than verifying
    the entire funsize tasks."""
    maxDiff = 30000

    def _do_common_assertions(self, graph):
        if graph["tasks"]:
            for t in graph["tasks"]:
                task = t["task"]
                self.assertEquals(task["priority"], "high")
                self.assertIn("task_name", task["extra"])

    def test_source_task_definition(self):
        graph = make_task_graph(
            source_enabled=True,
            repo_path="releases/foo",
            revision="fedcba654321",
            branch="foo",
            updates_enabled=False,
        )

        self._do_common_assertions(graph)

        task = get_task_by_name(graph, "foo_source")["task"]
        payload = task["payload"]
        self.assertEquals(task["provisionerId"], "aws-provisioner-v1")
        self.assertEquals(task["workerType"], "opt-linux64")
        self.assertTrue(payload["image"].startswith("taskcluster/desktop-build:"))
        self.assertTrue("cache" in payload)
        self.assertTrue("artifacts" in payload)
        self.assertTrue("env" in payload)
        self.assertTrue("command" in payload)

    def test_required_graph_scopes(self):
        graph = make_task_graph(
            updates_enabled=False,
            source_enabled=False,
        )

        self._do_common_assertions(graph)
        self.assertEquals(graph["tasks"], None)

        expected_scopes = set([
            "signing:format:gpg",
            "queue:define-task:buildbot-bridge/buildbot-bridge",
            "queue:create-task:buildbot-bridge/buildbot-bridge",
            "queue:task-priority:high",
        ])
        self.assertTrue(expected_scopes.issubset(graph["scopes"]))

    def test_funsize_en_US_deps(self):
        graph = make_task_graph(
            source_enabled=False,
            updates_enabled=True,
            l10n_platforms=None,
            enUS_platforms=["win32", "macosx64"],
            partial_updates={
                "38.0": {
                    "buildNumber": 1,
                },
                "37.0": {
                    "buildNumber": 2,
                },
            },
            branch="mozilla-beta",
            repo_path="releases/mozilla-beta",
            product="firefox",
            revision="abcdef123456",
            balrog_api_root="https://fake.balrog/api",
            signing_class="release-signing",
        )

        self._do_common_assertions(graph)

        for p in ("win32", "macosx64"):
            for v in ("38.0build1", "37.0build2"):
                generator = get_task_by_name(graph, "{}_en-US_{}_funsize_update_generator".format(p, v))
                signing = get_task_by_name(graph, "{}_en-US_{}_funsize_signing_task".format(p, v))
                balrog = get_task_by_name(graph, "{}_en-US_{}_funsize_balrog_task".format(p, v))

                self.assertIsNone(generator.get("requires"))
                self.assertEquals(signing.get("requires"), [generator["taskId"]])
                self.assertEquals(balrog.get("requires"), [signing["taskId"]])

    def test_funsize_en_US_scopes(self):
        graph = make_task_graph(
            source_enabled=False,
            updates_enabled=True,
            l10n_platforms=None,
            enUS_platforms=["win32", "macosx64"],
            partial_updates={
                "38.0": {
                    "buildNumber": 1,
                },
                "37.0": {
                    "buildNumber": 2,
                },
            },
            branch="mozilla-beta",
            product="firefox",
            revision="abcdef123456",
            balrog_api_root="https://fake.balrog/api",
            signing_class="release-signing",
        )

        self._do_common_assertions(graph)
        expected_scopes = set([
            "queue:*", "docker-worker:*", "scheduler:*",
            "signing:format:gpg", "signing:format:mar",
            "signing:cert:release-signing",
            "docker-worker:feature:balrogVPNProxy"
        ])
        self.assertTrue(expected_scopes.issubset(graph["scopes"]))

        for p in ("win32", "macosx64"):
            for v in ("38.0build1", "37.0build2"):
                generator = get_task_by_name(graph, "{}_en-US_{}_funsize_update_generator".format(p, v))
                signing = get_task_by_name(graph, "{}_en-US_{}_funsize_signing_task".format(p, v))
                balrog = get_task_by_name(graph, "{}_en-US_{}_funsize_balrog_task".format(p, v))

                self.assertIsNone(generator["task"].get("scopes"))
                self.assertItemsEqual(signing["task"]["scopes"], ["signing:cert:release-signing", "signing:format:mar", "signing:format:gpg"])
                self.assertItemsEqual(balrog["task"]["scopes"], ["docker-worker:feature:balrogVPNProxy"])

    def test_funsize_en_US_scopes_dep_signing(self):
        graph = make_task_graph(
            source_enabled=False,
            updates_enabled=True,
            l10n_platforms=None,
            enUS_platforms=["win32", "macosx64"],
            partial_updates={
                "38.0": {
                    "buildNumber": 1,
                },
                "37.0": {
                    "buildNumber": 2,
                },
            },
            branch="mozilla-beta",
            product="firefox",
            revision="abcdef123456",
            balrog_api_root="https://fake.balrog/api",
            signing_class="dep-signing",
        )

        self._do_common_assertions(graph)
        expected_scopes = set([
            "queue:*", "docker-worker:*", "scheduler:*",
            "signing:format:gpg", "signing:format:mar",
            "signing:cert:dep-signing",
        ])
        self.assertTrue(expected_scopes.issubset(graph["scopes"]))
        self.assertNotIn("docker-worker:feature:balrogVPNProxy", graph["scopes"])

        for p in ("win32", "macosx64"):
            for v in ("38.0build1", "37.0build2"):
                generator = get_task_by_name(graph, "{}_en-US_{}_funsize_update_generator".format(p, v))
                signing = get_task_by_name(graph, "{}_en-US_{}_funsize_signing_task".format(p, v))
                balrog = get_task_by_name(graph, "{}_en-US_{}_funsize_balrog_task".format(p, v))

                self.assertIsNone(generator["task"].get("scopes"))
                self.assertItemsEqual(signing["task"]["scopes"], ["signing:cert:dep-signing", "signing:format:mar", "signing:format:gpg"])
                self.assertIsNone(balrog["task"].get("scopes"))
