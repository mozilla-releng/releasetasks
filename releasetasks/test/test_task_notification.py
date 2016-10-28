import unittest
from releasetasks.test import PVT_KEY_FILE, verify
from releasetasks.test.firefox import make_task_graph, create_firefox_test_args
from voluptuous import Any, Schema


class TestFirefoxTaskNotifications(unittest.TestCase):

    def setUp(self):
        self.notifications_schema = Schema({
            'task': {
                'extra': {
                    #  Notification section is either 'no notifications' or the below schema
                    'notifications': Any(
                        Schema({
                            Any(
                                'task-completed',
                                'task-exception',
                                'task-failed',
                            ): {
                                    'subject': str,
                                    'message': str,
                            }
                        }, extra=True, required=True),
                        'no notifications'
                    )
                }
            }
        }, required=True, extra=True)
        test_kwargs = create_firefox_test_args({
            'source_enabled': True,
            'updates_enabled': True,
            'bouncer_enabled': True,
            'checksums_enabled': True,
            'push_to_candidates_enabled': True,
            'push_to_releases_enabled': True,
            'push_to_releases_automatic': True,
            'postrelease_version_bump_enabled': True,
            'postrelease_mark_as_shipped_enabled': True,
            'postrelease_bouncer_aliases_enabled': True,
            'release_channels': ['foo'],
            'final_verify_channels': ['foo'],
            'signing_pvt_key': PVT_KEY_FILE,
            'en_US_config': {
                "platforms": {
                    "macosx64": {"task_id": "abc"},
                    "win32": {"task_id": "def"},
                    "win64": {"task_id": "jgh"},
                    "linux": {"task_id": "ijk"},
                    "linux64": {"task_id": "lmn"},
                }
            },
        })
        self.graph = make_task_graph(**test_kwargs)

    def test_notification_configuration(self):
        for task in self.graph['tasks']:
            verify(task, self.notifications_schema)
