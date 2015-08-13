# -*- coding: utf-8 -*-
import unittest

from releasetasks import make_task_graph
from ..tcutils import stable_slug_id


def get_task_by_name(graph, name):
    for t in graph["tasks"]:
        if t["taskid"] == stable_slug_id(name):
            return t
    return None


def get_task_by_slugid(graph, slugid):
    for t in graph["tasks"]:
        if t["taskid"] == slugid:
            return t
    return None


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
                self.assertEquals("task_name" in task["extra"])

    def test_updates_disabled(self):
        graph = make_task_graph(
            updates_enabled=False
        )

        self._do_common_assertions(graph)
        self.assertEquals(graph["tasks"], None)
        self.assertEquals(graph["scopes"], None)

    def test_minimal_graph(self):
        """Tests a very minimal graph, with some platforms, l10n and other
        unnecessary tasks disabled."""
        graph = make_task_graph(
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
        self.assertEquals(graph, {})
