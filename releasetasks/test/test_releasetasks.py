# -*- coding: utf-8 -*-
import unittest


from releasetasks import make_task_graph

class TestMakeTaskGraph(unittest.TestCase):
    maxDiff = 30000

    def testSimpleGraph(self):
        # TODO: how to do this without manually rewriting insane amounts of template code?
        # maybe manually rewriting it is the right thing to do?
        expected = {
        }
        generated = make_task_graph(
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
        )
        self.assertEquals(expected, generated)
