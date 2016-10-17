import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args
from releasetasks.test import PVT_KEY_FILE
from voluptuous import Schema, truth
from voluptuous.humanize import validate_with_humanized_errors


@truth
def passes_graph_scopes_test(graph_scopes):
    expected_graph_scopes = {"queue:task-priority:high"}
    assert expected_graph_scopes.issubset(graph_scopes)
    return True


class TestBouncerAliases(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    human_task = None
    payload = None

    def setUp(self):
        self.GRAPH_SCHEMA = Schema({
            'scopes': passes_graph_scopes_test,
        }, required=True, extra=True)

        self.HUMAN_TASK_SCHEMA = Schema({
            'task': {
                'provisionerId': 'null-provisioner',
                'workerType': 'human-decision',
            }
        }, required=True, extra=True)

        self.TASK_SCHEMA = Schema({
            'task': {
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
        }, required=True, extra=True)

        test_kwargs = create_firefox_test_args({
            'postrelease_bouncer_aliases_enabled': True,
            'release_channels': ['foo'],
            'signing_pvt_key': PVT_KEY_FILE,
            'en_US_config': {
                "platforms": {
                    "macosx64": {},
                    "win32": {},
                    "win64": {},
                    "linux": {},
                    "linux64": {},
                }
            },
        })
        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(
            self.graph, "release-foo-firefox_bouncer_aliases")
        self.human_task = get_task_by_name(
            self.graph, "publish_release_human_decision")

    def test_human_task(self):
        assert validate_with_humanized_errors(self.human_task, self.HUMAN_TASK_SCHEMA)

    def test_task(self):
        assert validate_with_humanized_errors(self.task, self.TASK_SCHEMA)

    def test_graph(self):
        assert validate_with_humanized_errors(self.graph, self.GRAPH_SCHEMA)

    def test_common_assertions(self):
        do_common_assertions(self.graph)
