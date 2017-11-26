import unittest

from releasetasks.test.desktop import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args
from releasetasks.test import PVT_KEY_FILE, verify
from voluptuous import Schema, truth


class TestSchedulePublishBalrogNoETA(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    payload = None

    def setUp(self):
        self.task_schema = Schema({
            'task': {
                'provisionerId': 'buildbot-bridge',
                'workerType': 'buildbot-bridge',
                'payload': {
                    'properties': {
                        'balrog_api_root': 'https://balrog.real/api',
                        'channels': 'alpha, release-dev',
                        'schedule_at': None,
                    }
                }
            }
        }, extra=True, required=True)

        test_kwargs = create_firefox_test_args({
            'push_to_candidates_enabled': True,
            'push_to_releases_enabled': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'release_channels': ['foo'],
            'final_verify_channels': ['foo'],
            'publish_to_balrog_channels': ["release-dev", "alpha"],
            'en_US_config': {
                "platforms": {
                    "macosx64": {
                        "unsigned_task_id": "xyz", "signed_task_id": "xyx",
                        "repackage_task_id": "xyx",
                        "repackage-signing_task_id": "xyx", "ci_system": "tc"
                    },
                    "win32": {
                        "unsigned_task_id": "xyz", "signed_task_id": "xyx",
                        "repackage_task_id": "xyx",
                        "repackage-signing_task_id": "xyx", "ci_system": "tc"
                    },
                    "win64": {
                        "unsigned_task_id": "xyz", "signed_task_id": "xyx",
                        "repackage_task_id": "xyx",
                        "repackage-signing_task_id": "xyx", "ci_system": "tc"
                    },
                    "linux": {
                        "unsigned_task_id": "xyz", "signed_task_id": "xyx",
                        "ci_system": "tc"
                    },
                    "linux64": {
                        "unsigned_task_id": "xyz", "signed_task_id": "xyx",
                        "ci_system": "tc"
                    },
                }
            },
        })

        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(self.graph, "release-foo-firefox_schedule_publishing_in_balrog")

    # Returns a validator for task dependencies
    def generate_task_requires_validator(self):
        requires_sorted = sorted([get_task_by_name(self.graph, "publish_release_human_decision")["taskId"]])

        @truth
        def validate_task_requires(task):
            return sorted(task['requires']) == requires_sorted

        return validate_task_requires

    def test_schedule_publish_balrog_task(self):
        verify(self.task, self.task_schema, self.generate_task_requires_validator())

    def test_common_assertions(self):
        do_common_assertions(self.graph)


class TestSchedulePublishBalrog(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    payload = None

    def setUp(self):
        self.task_schema = Schema({
            'task': {
                'provisionerId': 'buildbot-bridge',
                'workerType': 'buildbot-bridge',
                'payload': {
                    'properties': {
                        'balrog_api_root': 'https://balrog.real/api',
                        'channels': 'alpha, release-dev',
                        'schedule_at': '2017-06-16T13:49:31.719007',
                    }
                }
            }
        }, extra=True, required=True)

        test_kwargs = create_firefox_test_args({
            'push_to_candidates_enabled': True,
            'push_to_releases_enabled': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'release_channels': ['foo'],
            'final_verify_channels': ['foo'],
            'publish_to_balrog_channels': ["release-dev", "alpha"],
            'en_US_config': {
                "platforms": {
                    "macosx64": {
                        "unsigned_task_id": "xyz", "signed_task_id": "xyx",
                        "repackage_task_id": "xyx",
                        "repackage-signing_task_id": "xyx", "ci_system": "tc"
                    },
                    "win32": {
                        "unsigned_task_id": "xyz", "signed_task_id": "xyx",
                        "repackage_task_id": "xyx",
                        "repackage-signing_task_id": "xyx", "ci_system": "tc"
                    },
                    "win64": {
                        "unsigned_task_id": "xyz", "signed_task_id": "xyx",
                        "repackage_task_id": "xyx",
                        "repackage-signing_task_id": "xyx", "ci_system": "tc"
                    },
                    "linux": {
                        "unsigned_task_id": "xyz", "signed_task_id": "xyx",
                        "ci_system": "tc"
                    },
                    "linux64": {
                        "unsigned_task_id": "xyz", "signed_task_id": "xyx",
                        "ci_system": "tc"
                    },
                }
            },
            'release_eta': '2017-06-16T13:49:31.719007',
        })

        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(self.graph, "release-foo-firefox_schedule_publishing_in_balrog")

    # Returns a validator for task dependencies
    def generate_task_requires_validator(self):
        requires_sorted = sorted([get_task_by_name(self.graph, "publish_release_human_decision")["taskId"]])

        @truth
        def validate_task_requires(task):
            return sorted(task['requires']) == requires_sorted

        return validate_task_requires

    def test_schedule_publish_balrog_task(self):
        verify(self.task, self.task_schema, self.generate_task_requires_validator())

    def test_common_assertions(self):
        do_common_assertions(self.graph)
