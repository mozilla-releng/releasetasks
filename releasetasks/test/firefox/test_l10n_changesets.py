import unittest

from releasetasks.test.firefox import do_common_assertions, get_task_by_name, \
    make_task_graph
from releasetasks.test import PVT_KEY_FILE, create_test_args


class TestL10NChangesets(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    task_beet = None

    def setUp(self):
        test_kwargs = create_test_args({
            'source_enabled': True,
            'push_to_candidates_enabled': True,
            'push_to_releases_enabled': True,
            'push_to_releases_automatic': True,
            'beetmover_candidates_bucket': 'mozilla-releng-beet-mover-dev',
            'branch': 'foo',
            'repo_path': 'releases/foo',
            'signing_pvt_key': PVT_KEY_FILE,
            'release_channels': ['foo', 'bar'],
            'partner_repacks_platforms': ['win32', 'linux'],
            'l10n_changesets': {"ab": "cd", "ef": "gh", "ij": "kl"},
            'en_US_config': {
                "platforms": {
                    "linux": {"task_id": "xyz"},
                    "win32": {"task_id": "xyy"},
                },
            }, 'l10n_config': {
                "platforms": {
                    "win32": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.exe",
                        "locales": ["de", "en-GB", "zh-TW"],
                        "chunks": 1,
                    },
                    "linux": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.tar.xz",
                        "locales": ["de", "en-GB", "zh-TW"],
                        "chunks": 1,
                    },

                },
                "changesets": {
                    "de": "default",
                    "en-GB": "default",
                    "zh-TW": "default",
                },
            },
        })
        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(self.graph, "foo_l10n_changeset")
        self.task_beet = get_task_by_name(self.graph, "foo_l10n_changeset_beet")

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_provisioner(self):
        self.assertEqual(self.task["task"]["provisionerId"], "aws-provisioner-v1")

    def test_worker_type(self):
        self.assertEqual(self.task["task"]["workerType"], "opt-linux64")

    def test_l10n_changesets_text(self):
        self.assertEqual(self.task["task"]["extra"]["l10n_changesets"],
                         "ab cd\nef gh\nij kl\n")
