import unittest

from releasetasks.test.firefox import do_common_assertions, get_task_by_name, \
    make_task_graph
from releasetasks.test import PVT_KEY_FILE, verify
from releasetasks.test.firefox import create_firefox_test_args
from voluptuous import Schema


class TestL10NChangesets(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None

    def setUp(self):
        self.task_schema = Schema({
            'task': {
                'workerType': 'opt-linux64',
                'provisionerId': 'aws-provisioner-v1',
                'extra': {
                    'l10n_changesets': 'ab cd\nef gh\nij kl\n',
                },
            },
        }, extra=True, required=True)

        test_kwargs = create_firefox_test_args({
            'source_enabled': True,
            'push_to_candidates_enabled': True,
            'push_to_releases_enabled': True,
            'push_to_releases_automatic': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'release_channels': ['foo', 'bar'],
            'partner_repacks_platforms': ['win32', 'linux'],
            'l10n_changesets': {"ab": "cd", "ef": "gh", "ij": "kl"},
            'en_US_config': {
                "platforms": {
                    "linux": {"task_id": "xyz"},
                    "win32": {"task_id": "xyy"},
                },
            },
            'l10n_config': {
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

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_task_schema(self):
        verify(self.task, self.task_schema)
