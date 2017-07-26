import unittest

from releasetasks.test.desktop import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args
from releasetasks.test import generate_scope_validator, PVT_KEY_FILE, verify
from voluptuous import Schema, truth


class TestBinaryTransparency(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    payload = None

    def setUp(self):
        self.graph_schema = Schema({
            'scopes': generate_scope_validator(scopes={'queue:task-priority:high'}),
        }, extra=True, required=True)

        self.test_schema = Schema({
            'task': {
                'provisionerId': 'scriptworker-prov-v1',
                'workerType': 'dummy-worker-transpar',
                'payload': {
                    'version': '42.0b2',
                    'chain': 'TRANSPARENCY.pem',
                    'contact': 'btang@mozilla.com',
                    'maxRunTime': 600,
                    'stage-product': 'firefox',
                    'summary': 'https://archive.mozilla.org/pub/firefox/candidates/42.0b2-candidates/build3/SHA256SUMMARY',
                }
            }
        }, extra=True, required=True)

        test_kwargs = create_firefox_test_args({
            'push_to_candidates_enabled': True,
            'checksums_enabled': True,
            'binary_transparency_enabled': True,
            'updates_enabled': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'accepted_mar_channel_id': 'firefox-mozilla-beta',
            'signing_cert': 'dep',
            'moz_disable_mar_cert_verification': True,
            'release_channels': ['foo'],
            'final_verify_channels': ['foo'],
            'en_US_config': {
                "platforms": {
                    "macosx64": {'signed_task_id': 'abc', 'unsigned_task_id': 'abc', 'repackage_task_id': 'xyx',
                                 'repackage-signing_task_id': 'xyx', 'ci_system': 'tc'},
                    "win64": {'signed_task_id': 'abc', 'unsigned_task_id': 'abc', 'repackage_task_id': 'xyx',
                              'repackage-signing_task_id': 'xyx', 'ci_system': 'tc'},
                    "linux64": {'signed_task_id': 'abc', 'unsigned_task_id': 'abc', 'repackage_task_id': 'xyx',
                                'repackage-signing_task_id': 'xyx', 'ci_system': 'tc'},
                }
            },
        })
        self.graph = make_task_graph(**test_kwargs)

        self.task = get_task_by_name(self.graph, "release-foo-firefox_binary_transparency")

    @staticmethod
    @truth
    def not_allowed(task):
        return 'scopes' not in task

    # Returns validator for task dependencies
    def generate_task_dependency_validator(self):
        requires = [get_task_by_name(self.graph, "release-foo-firefox_chcksms")["taskId"]]

        @truth
        def validate_dependencies(task):
            return sorted(task['requires']) == sorted(requires)

        return validate_dependencies

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_task(self):
        verify(self.task, self.test_schema, self.generate_task_dependency_validator(),
               TestBinaryTransparency.not_allowed)

    def test_graph(self):
        verify(self.graph, self.graph_schema)
