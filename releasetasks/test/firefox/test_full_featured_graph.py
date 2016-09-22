import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, create_firefox_test_args
from releasetasks.test import PVT_KEY_FILE


class TestFullGraph(unittest.TestCase):
    maxDiff = 30000
    graph = None

    def setUp(self):
        test_args = create_firefox_test_args({
            'source_enabled': True,
            'checksums_enabled': True,
            'updates_enabled': True,
            'bouncer_enabled': True,
            'push_to_candidates_enabled': True,
            'push_to_releases_enabled': True,
            'uptake_monitoring_enabled': True,
            'postrelease_version_bump_enabled': True,
            'postrelease_mark_as_shipped_enabled': True,
            'postrelease_bouncer_aliases_enabled': True,
            'push_to_releases_automatic': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'publish_to_balrog_channels': ['foo'],
            'partner_repacks_platforms': [
                'win32',
                'macosx64',
            ],
            'en_US_config': {
                "platforms": {
                    "macosx64": {"task_id": "abc"},
                    "win32": {"task_id": "def"},
                    "win64": {"task_id": "jgh"},
                    "linux": {"task_id": "ijk"},
                    "linux64": {"task_id": "lmn"},
                }
            }
        })
        self.graph = make_task_graph(**test_args)

    def test_common_assertions(self):
        do_common_assertions(self.graph)
