import unittest
from releasetasks.test import PVT_KEY_FILE
from releasetasks.test.firefox import make_task_graph


class TestTaskNotifications(unittest.TestCase):

    def setUp(self):
        self.graph = make_task_graph(
            version="42.0b2",
            next_version="42.0b3",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=True,
            en_US_config={
                "platforms": {
                    "macosx64": {"task_id": "abc"},
                    "win32": {"task_id": "def"},
                    "win64": {"task_id": "jgh"},
                    "linux": {"task_id": "ijk"},
                    "linux64": {"task_id": "lmn"},
                }
            },
            l10n_config={},
            repo_path="releases/foo",
            build_tools_repo_path='build/tools',
            product="firefox",
            revision="fedcba654321",
            mozharness_changeset="abcd",
            partial_updates={
                "38.0": {
                    "buildNumber": 1,
                    "locales": ["de", "en-GB", "zh-TW"],
                },
                "37.0": {
                    "buildNumber": 2,
                    "locales": ["de", "en-GB", "zh-TW"],
                },
            },
            branch="foo",
            updates_enabled=True,
            bouncer_enabled=True,
            checksums_enabled=True,
            push_to_candidates_enabled=True,
            beetmover_candidates_bucket='mozilla-releng-beet-mover-dev',
            push_to_releases_enabled=True,
            push_to_releases_automatic=True,
            uptake_monitoring_enabled=False,
            postrelease_version_bump_enabled=True,
            postrelease_mark_as_shipped_enabled=True,
            postrelease_bouncer_aliases_enabled=True,
            tuxedo_server_url="https://bouncer.real.allizom.org/api",
            signing_class="release-signing",
            release_channels=["foo"],
            final_verify_channels=["foo"],
            balrog_api_root="https://balrog.real/api",
            funsize_balrog_api_root="http://balrog/api",
            signing_pvt_key=PVT_KEY_FILE,
            publish_to_balrog_channels=None,
        )

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
