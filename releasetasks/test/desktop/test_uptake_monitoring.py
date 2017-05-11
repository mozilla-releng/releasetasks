import unittest

from releasetasks.test.desktop import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args
from releasetasks.test import PVT_KEY_FILE, verify
from voluptuous import Schema, truth


class TestUptakeMonitoring(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    payload = None

    def setUp(self):
        self.task_schema = Schema({
            'task': {
                'scopes': list,
                'provisionerId': 'buildbot-bridge',
                'workerType': 'buildbot-bridge',
                'payload': {
                    'properties': {
                        'product': 'firefox',
                        'version': '42.0b2',
                        'build_number': 3,
                        'repo_path': 'releases/foo',
                        'script_repo_revision': 'abcd',
                        'revision': 'abcdef123456',
                        'tuxedo_server_url': 'https://bouncer.real.allizom.org/api',
                    }
                }
            }
        }, extra=True, required=True)

        test_kwargs = create_firefox_test_args({
            'push_to_candidates_enabled': True,
            'push_to_releases_enabled': True,
            'uptake_monitoring_enabled': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'uptake_monitoring_platforms': ["macosx64", "win32", "win64", "linux", "linux64"],
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
        })
        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(self.graph, "release-foo-firefox_uptake_monitoring")
        self.payload = self.task["task"]["payload"]

    def generate_task_dependency_validator(self):
        requires = sorted([get_task_by_name(self.graph, "release-foo_firefox_push_to_releases")["taskId"]])

        @truth
        def validate_task_dependencies(task):
            return sorted(requires) == sorted(task['requires'])

        return validate_task_dependencies

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_uptake_monitoring_task(self):
        verify(self.task, self.task_schema, self.generate_task_dependency_validator())


class TestUptakeMonitoringSHA1(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    payload = None

    def setUp(self):
        test_kwargs = create_firefox_test_args({
            'push_to_candidates_enabled': True,
            'push_to_releases_enabled': True,
            'uptake_monitoring_enabled': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'uptake_monitoring_platforms': ["macosx64", "win32", "win64", "linux", "linux64"],
            'partner_repacks_platforms': [],
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
        self.task = get_task_by_name(self.graph, "release-foo-firefox_uptake_monitoring")

    # Returns a validator for task dependencies
    def generate_task_requires_validator(self):
        requires = [
            get_task_by_name(self.graph, "release-foo_firefox_push_to_releases")["taskId"],
            get_task_by_name(self.graph, "release-foo-firefox_partner_repacks_copy_to_releases")["taskId"],
        ]

        @truth
        def validate_task_requires(task):
            return sorted(requires) == sorted(task['requires'])

        return validate_task_requires

    def test_task(self):
        verify(self.task, self.generate_task_requires_validator())
