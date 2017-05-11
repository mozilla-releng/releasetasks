import unittest

from releasetasks.test.desktop import make_task_graph, do_common_assertions, \
    get_task_by_name
from releasetasks.test import generate_scope_validator, PVT_KEY_FILE, verify
from releasetasks.test.desktop import create_firefox_test_args
from voluptuous import Match, Schema, truth


class TestFinalVerification(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task_def = None
    task = None
    payload = None

    def setUp(self):
        self.task_schema = Schema({
            'task': {
                'provisionerId': 'aws-provisioner-v1',
                'workerType': 'b2gtest',
                'payload': {
                    'command': [str],
                    'env': dict,
                    'image': Match(r'^rail/python-test-runner'),
                }
            }
        }, extra=True, required=True)

        self.graph_schema = Schema({
            'scopes': generate_scope_validator(scopes={'queue:task-priority:high'}),
        }, extra=True, required=True)

        test_args = create_firefox_test_args({
            'push_to_releases_enabled': True,
            'uptake_monitoring_enabled': True,
            'release_channels': ['foo'],
            'final_verify_channels': ['foo'],
            'final_verify_platforms': ["macosx64", "win32", "win64", "linux", "linux64"],
            'enUS_platforms': ["linux", "linux64", "win64", "win32", "macosx64"],
            'signing_pvt_key': PVT_KEY_FILE,
            'accepted_mar_channel_id': 'firefox-mozilla-beta',
            'signing_cert': 'dep',
            'moz_disable_mar_cert_verification': True,
            'en_US_config': {
                "platforms": {
                    "macosx64": {},
                    "win32": {},
                    "win64": {},
                    "linux": {},
                    "linux64": {},
                },
            },
        })
        self.graph = make_task_graph(**test_args)
        self.task = get_task_by_name(self.graph, "foo_final_verify")

    @staticmethod
    @truth
    def not_allowed(task):
        for key in ('scopes', 'cache', 'artifacts',):
            if key in task:
                return False
        else:
            return True

    # Returns validator for task dependencies
    def generate_task_dependency_validator(self):
        requires = [get_task_by_name(self.graph, "release-foo-firefox_uptake_monitoring")["taskId"]]

        @truth
        def validate_dependencies(task):
            return sorted(task['requires']) == sorted(requires)

        return validate_dependencies

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_task(self):
        verify(self.task, self.task_schema, self.generate_task_dependency_validator(), TestFinalVerification.not_allowed)


class TestFinalVerificationMultiChannel(unittest.TestCase):
    maxDiff = 30000
    graph = None

    def setUp(self):
        self.graph_schema = Schema({
            'scopes': generate_scope_validator(scopes={'queue:task-priority:high'})
        }, extra=True, required=True)

        self.task_schema = Schema({
            'task': {
                'provisionerId': 'aws-provisioner-v1',
                'workerType': 'b2gtest',
                'payload': {
                    'image': Match(r'^rail/python-test-runner'),
                    'command': [str],
                    'env': dict,
                }
            }
        }, extra=True, required=True)

        test_kwargs = create_firefox_test_args({
            'push_to_releases_enabled': True,
            'release_channels': ['beta', 'release'],
            'final_verify_channels': ['beta', 'release'],
            'final_verify_platforms': ["macosx64", "win32", "win64", "linux", "linux64"],
            'signing_pvt_key': PVT_KEY_FILE,
            'accepted_mar_channel_id': 'firefox-mozilla-beta',
            'signing_cert': 'dep',
            'moz_disable_mar_cert_verification': True,
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
        self.tasks = [get_task_by_name(self.graph, "{chan}_final_verify".format(chan=chan)) for chan in ('beta', 'release',)]

    @staticmethod
    @truth
    def not_allowed(task):
        if 'scopes' in task:
            return False

        for key in ('cache', 'artifacts',):
            if key in task['task']['payload']:
                return False
        else:
            return True

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_graph(self):
        verify(self.graph, self.graph_schema)

    def test_tasks(self):
        for task in self.tasks:
            verify(task, self.task_schema, TestFinalVerificationMultiChannel.not_allowed)


class TestFinalVerifyNoMirrors(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task_def = None
    task = None
    payload = None

    def setUp(self):
        test_kwargs = create_firefox_test_args({
            'updates_enabled': True,
            'push_to_candidates_enabled': True,
            'repo_path': 'releases/mozilla-beta',
            'branch': 'mozilla-beta',
            'signing_pvt_key': PVT_KEY_FILE,
            'accepted_mar_channel_id': 'firefox-mozilla-beta',
            'signing_cert': 'dep',
            'moz_disable_mar_cert_verification': True,
            'enUS_platforms': ["win32", "macosx64"],
            'final_verify_platforms': ["macosx64", "win32"],
            'release_channels': ['beta'],
            'final_verify_channels': ['beta'],
            'en_US_config': {
                "platforms": {
                    "macosx64": {'signed_task_id': 'abc', 'unsigned_task_id': 'abc'},
                    "win32": {'signed_task_id': 'abc', 'unsigned_task_id': 'abc'},
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
                    "macosx64": {
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
        self.task = get_task_by_name(self.graph, "beta_final_verify")

    # Returns validator for task dependencies
    def generate_task_dependency_validator(self):
        en_US_tmpl = "release-mozilla-beta_firefox_{}_complete_en-US_beetmover_candidates"
        en_US_partials_tmpl = "release-mozilla-beta_firefox_{}_partial_en-US_{}build{}_beetmover_candidates"
        l10n_tmpl = "release-mozilla-beta_firefox_{}_l10n_repack_beetmover_candidates_1"
        l10n_partials_tmpl = "release-mozilla-beta_firefox_{}_l10n_repack_partial_{}build{}_beetmover_candidates_1"
        requires = []
        for completes in (en_US_tmpl, l10n_tmpl):
            requires.extend([
                                get_task_by_name(self.graph, completes.format(p))["taskId"]
                                for p in ("macosx64", "win32")
                                ])
        for partials in (en_US_partials_tmpl, l10n_partials_tmpl):
            requires.extend([
                                get_task_by_name(self.graph, partials.format(platform, p_version, p_build_num))[
                                    "taskId"]
                                for platform in ("macosx64", "win32")
                                for p_version, p_build_num in (('38.0', '1'), ('37.0', '2'))
                                ])

        @truth
        def validate_dependencies(task):
            return sorted(requires) == sorted(task['requires'])

        return validate_dependencies

    def test_task(self):
        verify(self.task, self.generate_task_dependency_validator())
