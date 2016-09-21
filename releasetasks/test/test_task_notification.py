import unittest
from releasetasks.test import PVT_KEY_FILE, create_test_args
from releasetasks.test.firefox import make_task_graph


class TestTaskNotifications(unittest.TestCase):

    def setUp(self):
        test_kwargs = create_test_args({
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
            'beetmover_candidates_bucket': 'mozilla-releng-beet-mover-dev',
            'repo_path': 'releases/foo',
            'branch': 'foo',
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

    def test_notifications_exist(self):
        for task in self.graph['tasks']:
            name = task['task']['metadata']['name']

            #  Make sure the extra/notifications section is present
            self.assertTrue('notifications' in task['task']['extra'],
                            'No extra/notifications section in task {name}'.format(name=name))

    def test_subject_exists(self):
        for task in self.graph['tasks']:
            name = task['task']['metadata']['name']
            if isinstance(task['task']['extra']['notifications'], dict):
                for exchange in task['task']['extra']['notifications'].values():
                    self.assertTrue('subject' in exchange,
                                    'No subject in {exchange} notification section for {name}'.format(exchange=exchange,
                                                                                                      name=name))

    def test_message_exists(self):
        for task in self.graph['tasks']:
            name = task['task']['metadata']['name']
            if isinstance(task['task']['extra']['notifications'], dict):
                for exchange in task['task']['extra']['notifications'].values():
                    self.assertTrue('message' in exchange,
                                    'No subject in {exchange} notification section for {name}'.format(exchange=exchange,
                                                                                                      name=name))

    def test_no_notification_string(self):
        for task in self.graph['tasks']:
            name = task['task']['metadata']['name']
            if isinstance(task['task']['extra']['notifications'], str):
                self.assertEquals(task['task']['extra']['notifications'], 'no notifications',
                                  'Notifications section for {task} is string, should be \'no notifications\' not {wrong_string}'
                                  .format(wrong_string=task['task']['extra']['notifications'], task=name))
