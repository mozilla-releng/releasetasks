import unittest

from releasetasks.test.desktop import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args
from releasetasks.test import PVT_KEY_FILE, verify
from voluptuous import Schema, truth


L10N_CONFIG = {
    'platforms': {
        'win32': {
            'en_us_binary_url': 'https://queue.taskcluster.net/something/firefox.exe',
            "mar_tools_url": "https://queue.taskcluster.net/something/",
            'locales': ['de', 'en-GB', 'zh-TW'],
            'chunks': 1
        },
        'win64': {
            'en_us_binary_url': 'https://queue.taskcluster.net/something/firefox.exe',
            "mar_tools_url": "https://queue.taskcluster.net/something/",
            'locales': ['de', 'en-GB', 'zh-TW'],
            'chunks': 1
        },
        'macosx64': {
            'en_us_binary_url': 'https://queue.taskcluster.net/something/firefox.exe',
            "mar_tools_url": "https://queue.taskcluster.net/something/",
            'locales': ['de', 'en-GB', 'zh-TW'],
            'chunks': 1
        },
    },
    'changesets': {
        'de': 'default',
        'en-GB': 'default',
        'zh-TW': 'default',
    }
}

EN_US_CONFIG = {
    'platforms': {
        'macosx64': {'signed_task_id': 'abc', 'unsigned_task_id': 'abc'},
        'win32': {'signed_task_id': 'abc', 'unsigned_task_id': 'abc'},
        'win64': {'signed_task_id': 'abc', 'unsigned_task_id': 'abc'},
    }
}


class TestEmailLocaltest(unittest.TestCase):
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
                    'name': 'firefox email release-drivers foo-localtest',
                },
                'extra': {
                    'notifications': {
                        'task-completed': {
                            'subject': 'firefox foo 42.0b2 updates are available on the foo-localtest channel now <EOM>',
                            'message': 'firefox foo 42.0b2 updates are available on the foo-localtest channel now <EOM>',
                            'ids': ['release-drivers'],
                        },
                    },
                },
            },
        }, extra=True, required=True)

        test_kwargs = create_firefox_test_args({
            'updates_enabled': True,
            'push_to_candidates_enabled': True,
            'push_to_releases_enabled': True,
            'push_to_releases_automatic': False,
            'update_verify_enabled': True,
            'updates_builder_enabled': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'branch': 'foo',
            'release_channels': ['foo'],
            'final_verify_channels': ['foo'],
            'l10n_config': L10N_CONFIG,
            'en_US_config': EN_US_CONFIG,
            'uptake_monitoring_enabled': True,
            'update_verify_channel': 'foo-cdntest',
            'update_verify_requires_cdn_push': True,
            'accepted_mar_channel_id': 'firefox-mozilla-beta',
            'signing_cert': 'dep',
            'moz_disable_mar_cert_verification': True,
        })

        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(self.graph, 'release-foo-firefox_email_foo-localtest')

    def generate_task_requires_validator(self):
        requires_sorted = sorted(
            get_task_by_name(self.graph, "release-foo_firefox_{}_update_verify_foo_{}".format(platform, i))["taskId"]
            for i in range(1, 13)
            for platform in ('win32', 'win64', 'macosx64')
        )

        @truth
        def validate_task_requires(task):
            return sorted(task['requires']) == requires_sorted

        return validate_task_requires

    def test_email_localtest(self):
        verify(self.task, self.task_schema, self.generate_task_requires_validator())

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_beta_is_excluded(self):
        test_kwargs = create_firefox_test_args({
            'updates_enabled': True,
            'push_to_candidates_enabled': True,
            'push_to_releases_enabled': True,
            'push_to_releases_automatic': True,
            'update_verify_enabled': True,
            'updates_builder_enabled': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'branch': 'beta',
            'release_channels': ['beta'],
            'final_verify_channels': ['beta'],
            'l10n_config': L10N_CONFIG,
            'en_US_config': EN_US_CONFIG,
            'uptake_monitoring_enabled': True,
            'update_verify_channel': 'beta-cdntest',
            'update_verify_requires_cdn_push': True,
            'accepted_mar_channel_id': None,
            'signing_cert': 'dep',
            'moz_disable_mar_cert_verification': True,
        })

        graph = make_task_graph(**test_kwargs)
        self.assertIsNone(get_task_by_name(graph, 'release-foo-firefox_email_foo-localtest'))
