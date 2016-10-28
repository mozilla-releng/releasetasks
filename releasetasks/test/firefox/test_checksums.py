import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args
from releasetasks.test import generate_scope_validator, PVT_KEY_FILE, verify
from voluptuous import Schema, truth


class TestChecksums(unittest.TestCase):
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
                'provisionerId': 'buildbot-bridge',
                'workerType': 'buildbot-bridge',
                'payload': {
                    'properties': {
                        'version': '42.0b2',
                        'build_number': 3,
                    }
                }
            }
        }, extra=True, required=True)

        test_kwargs = create_firefox_test_args({
            'push_to_candidates_enabled': True,
            'checksums_enabled': True,
            'updates_enabled': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'release_channels': ['foo'],
            'final_verify_channels': ['foo'],
            'en_US_config': {
                "platforms": {
                    "macosx64": {"task_id": "abc"},
                    "win64": {"task_id": "jgh"},
                    "linux64": {"task_id": "lmn"},
                }
            },
        })
        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(self.graph, "release-foo-firefox_chcksms")

    @staticmethod
    @truth
    def not_allowed(task):
        return 'scopes' not in task

    # Returns validator for task dependencies
    def generate_task_dependency_validator(self):
        tmpl = "release-foo_firefox_{p}_complete_en-US_beetmover_candidates"
        tmpl_partials = "release-foo_firefox_{p}_partial_en-US_{v}build{b}_beetmover_candidates"
        requires = [
            get_task_by_name(self.graph, tmpl.format(p=p))["taskId"]
            for p in ("linux64", "macosx64", "win64")
        ] + [
            get_task_by_name(self.graph, tmpl_partials.format(p=p, v=v, b=b))["taskId"]
            for p in ("linux64", "macosx64", "win64")
            for v, b in [("37.0", 2), ("38.0", 1)]
        ]

        @truth
        def validate_dependencies(task):
            return sorted(task['requires']) == sorted(requires)

        return validate_dependencies

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_task(self):
        verify(self.task, self.test_schema, self.generate_task_dependency_validator(), TestChecksums.not_allowed)

    def test_graph(self):
        verify(self.graph, self.graph_schema)
