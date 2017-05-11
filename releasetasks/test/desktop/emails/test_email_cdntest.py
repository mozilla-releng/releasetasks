import unittest

from releasetasks.test.desktop import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args
from releasetasks.test import PVT_KEY_FILE, verify
from voluptuous import Schema, truth


class TestEmailFinal(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    payload = None

    def setUp(self):
        self.task_schema = Schema({
            'task': {
                'provisionerId': 'aws-provisioner-v1',
                'workerType': 'gecko-decision',
                'payload': {
                    'command': ['/bin/echo', 'Dummy task to tell pulse-notify to send an email'],
                },
                'metadata': {
                    'name': 'firefox email release-drivers foo-cdntest',
                },
                'extra': {
                    'notifications': {
                        'task-completed': {
                            'subject': 'firefox foo 42.0b2 updates are available on the foo-cdntest channel now <EOM>',
                            'message': 'firefox foo 42.0b2 updates are available on the foo-cdntest channel now <EOM>',
                            'ids': ['release-drivers'],
                        },
                    },
                },
            },
        }, extra=True, required=True)

        test_kwargs = create_firefox_test_args({
            'push_to_candidates_enabled': True,
            'push_to_releases_enabled': True,
            'uptake_monitoring_enabled': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'uptake_monitoring_platforms': ["macosx64", "win32", "win64", "linux", "linux64"],
            'partner_repacks_platforms': [],
            'accepted_mar_channel_id': 'firefox-mozilla-beta',
            'signing_cert': 'dep',
            'moz_disable_mar_cert_verification': True,
            'eme_free_repacks_platforms': [],
            'sha1_repacks_platforms': ['win32'],
            'release_channels': ['foo'],
            'final_verify_channels': ['foo'],
            'en_US_config': {
                "platforms": {
                    "macosx64": {'signed_task_id': 'abc', 'unsigned_task_id': 'abc'},
                    "win32": {'signed_task_id': 'abc', 'unsigned_task_id': 'abc'},
                    "win64": {'signed_task_id': 'abc', 'unsigned_task_id': 'abc'},
                    "linux": {'signed_task_id': 'abc', 'unsigned_task_id': 'abc'},
                    "linux64": {'signed_task_id': 'abc', 'unsigned_task_id': 'abc'},
                }
            },
            'l10n_config': {
                "platforms": {
                    "win32": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.exe",
                        "mar_tools_url": "https://queue.taskcluster.net/something/",
                        "locales": ["de", "en-GB", "zh-TW"],
                        "chunks": 1,
                    },
                    "linux64": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.tar.xz",
                        "mar_tools_url": "https://queue.taskcluster.net/something/",
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
        self.task = get_task_by_name(self.graph, "release-foo-firefox_publish_balrog")
        self.task = get_task_by_name(self.graph, "release-foo-firefox_email_foo-cdntest")

    def generate_task_requires_validator(self):
        requires_sorted = sorted([get_task_by_name(self.graph, "release-foo-firefox_uptake_monitoring")["taskId"]])

        @truth
        def validate_task_requires(task):
            return sorted(task['requires']) == requires_sorted

        return validate_task_requires

    def test_email_cdntest(self):
        verify(self.task, self.task_schema, self.generate_task_requires_validator())

    def test_common_assertions(self):
        do_common_assertions(self.graph)
