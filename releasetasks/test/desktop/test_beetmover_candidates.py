import unittest

from releasetasks.test.desktop import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args
from releasetasks.test import generate_scope_validator, PVT_KEY_FILE, verify
from releasetasks.util import buildbot2ftp
from voluptuous import Schema, truth


EN_US_CONFIG = {
    "platforms": {
        "macosx64": {"unsigned_task_id": "xyz", "signed_task_id": "xyx"},
        "win32": {"unsigned_task_id": "xyz", "signed_task_id": "xyx"},
    }
}


class BaseTestBeetmoverCandidates(object):

    GRAPH_SCHEMA = Schema({
        'scopes': generate_scope_validator(scopes={
            'queue:task-priority:high',
            'queue:define-task:aws-provisioner-v1/gecko-3-b-linux',
            'queue:create-task:aws-provisioner-v1/gecko-3-b-linux',
        })
    }, extra=True, required=True)

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    @staticmethod
    @truth
    def not_allowed(task):
        return 'scopes' not in task


class TestBeetmoverEnUSCandidates(unittest.TestCase, BaseTestBeetmoverCandidates):
    maxDiff = 30000
    graph = None
    # we will end up with one task for each platform
    tasks = None

    def setUp(self):
        self.task_schema = Schema({
            'task': {
                'provisionerId': 'aws-provisioner-v1',
                'workerType': 'gecko-3-b-linux',
                'extra': {
                    'build_props': {
                        'product': 'firefox',
                        'locales': ['en-US'],
                        'branch': 'mozilla-beta',
                        'version': '42.0b2',
                        'revision': 'abcdef123456',
                        'platform': str,
                    }
                }
            }
        }, extra=True, required=True)

        test_kwargs = create_firefox_test_args({
            'push_to_candidates_enabled': True,
            'en_US_config': EN_US_CONFIG,
            'branch': "mozilla-beta",
            'repo_path': "releases/mozilla-beta",
            'signing_pvt_key': PVT_KEY_FILE,
            'build_tools_repo_path': 'build/tools',
            'accepted_mar_channel_id': 'firefox-mozilla-beta',
            'signing_cert': 'dep',
            'moz_disable_mar_cert_verification': True,
        })
        self.graph = make_task_graph(**test_kwargs)

        self.tasks = {
            'win32': get_task_by_name(
                self.graph, "release-{}_{}_{}_complete_en-US_beetmover_candidates".format(
                    "mozilla-beta", "firefox", 'win32'
                )
            ),
            'macosx64': get_task_by_name(
                self.graph, "release-{}_{}_{}_complete_en-US_beetmover_candidates".format(
                    "mozilla-beta", "firefox", 'macosx64'
                )
            ),
        }

    # This function returns a validator function to check the command requirements for each platform
    def generate_command_requirements_validator(self, platform):
        @truth
        def validate_command_requirements(task):
            command = ''.join(task['task']['payload']['command'])
            required_elements = (
                "--app-version 42.0",
                "--locale en-US",
                "--bucket fake_bucket",
                "--taskid {}".format(EN_US_CONFIG['platforms'][platform]['signed_task_id']),
                "--platform {}".format(buildbot2ftp(platform)),
                "--version 42.0b2",
            )
            for element in required_elements:
                if element not in command:
                    return False
            else:
                return True

        return validate_command_requirements

    def test_tasks(self):
        for platform, task in self.tasks.iteritems():
            verify(task, self.task_schema, self.generate_command_requirements_validator(platform), TestBeetmoverEnUSCandidates.not_allowed)


class TestBeetmover110nCandidates(unittest.TestCase, BaseTestBeetmoverCandidates):
    maxDiff = 30000
    graph = None
    # we will end up with one task for each platform
    tasks = None
    l10n_config = {
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
    }

    def setUp(self):
        self.task_schema = Schema({
            'task': {
                'provisionerId': 'aws-provisioner-v1',
                'workerType': 'gecko-3-b-linux',
                'extra': {
                    'build_props': {
                        'product': 'firefox',
                        'locales': ["de", "en-GB", "zh-TW"],
                        'branch': 'mozilla-beta',
                        'version': '42.0b2',
                        'revision': 'abcdef123456',
                        'platform': str,
                    }
                }
            }
        }, extra=True, required=True)

        test_kwargs = create_firefox_test_args({
            'push_to_candidates_enabled': True,
            'branch': 'mozilla-beta',
            'repo_path': 'releases/mozilla-beta',
            'release_channels': ['beta'],
            'final_verify_channels': ['beta'],
            'signing_pvt_key': PVT_KEY_FILE,
            'accepted_mar_channel_id': 'firefox-mozilla-beta',
            'signing_cert': 'dep',
            'moz_disable_mar_cert_verification': True,
            'en_US_config': EN_US_CONFIG,
            'l10n_config': self.l10n_config,
        })

        self.graph = make_task_graph(**test_kwargs)
        self.tasks = {
            'win32': get_task_by_name(
                self.graph, "release-{}_{}_{}_l10n_repack_beetmover_candidates_1".format("mozilla-beta",
                                                                                         "firefox",
                                                                                         'win32')
            ),
            'macosx64': get_task_by_name(
                self.graph, "release-{}_{}_{}_l10n_repack_beetmover_candidates_1".format("mozilla-beta",
                                                                                         "firefox",
                                                                                         'macosx64')
            ),
        }

    # This function returns a validator function to check the command requirements for each platform
    def generate_command_requirements_validator(self, platform):
        l10n_artifact_task = get_task_by_name(
            self.graph,
            "release-mozilla-beta_firefox_{}_l10n_repack_artifacts_1".format(platform)
        )

        task_id = l10n_artifact_task['taskId']

        @truth
        def verify_command_requirements(task):
            command = ''.join(task['task']['payload']['command'])
            required_elements = (
                "--app-version 42.0",
                "--locale de --locale en-GB --locale zh-TW",
                "--bucket fake_bucket",
                "--taskid {}".format(task_id),
                "--platform {}".format(buildbot2ftp(platform)),
                "--version 42.0b2",
            )

            for element in required_elements:
                if element not in command:
                    return False
            else:
                return True

        return verify_command_requirements

    def test_tasks(self):
        for platform, task in self.tasks.iteritems():
            verify(task, self.task_schema, self.generate_command_requirements_validator(platform), TestBeetmover110nCandidates.not_allowed)


class TestBeetmoverEnUSPartialsCandidates(unittest.TestCase, BaseTestBeetmoverCandidates):
    maxDiff = 30000
    graph = None
    # we will end up with one task for each platform
    tasks = None

    def setUp(self):
        self.task_schema = Schema({
            'task': {
                'provisionerId': 'aws-provisioner-v1',
                'workerType': 'gecko-3-b-linux',
            }
        }, extra=True, required=True)

        test_kwargs = create_firefox_test_args({
            'updates_enabled': True,
            'push_to_candidates_enabled': True,
            'branch': 'mozilla-beta',
            'repo_path:': 'mozilla/beta',
            'signing_pvt_key': PVT_KEY_FILE,
            'en_US_config': EN_US_CONFIG,
            'accepted_mar_channel_id': 'firefox-mozilla-beta',
            'signing_cert': 'dep',
            'moz_disable_mar_cert_verification': True,
        })
        self.graph = make_task_graph(**test_kwargs)

        self.tasks = {
            'win32': get_task_by_name(
                self.graph, "release-{}_{}_{}_partial_en-US_{}build{}_beetmover_candidates".format(
                    "mozilla-beta", "firefox", 'win32', "38.0", 1
                )
            ),
            'macosx64': get_task_by_name(
                self.graph, "release-{}_{}_{}_partial_en-US_{}build{}_beetmover_candidates".format(
                    "mozilla-beta", "firefox", 'macosx64', "37.0", 2
                )
            ),
        }

    # This function returns a validator function to check the command requirements for each platform
    def generate_command_requirements_validator(self, platform):
        # Command requirements for win32
        if platform == 'win32':
            buildername = "win32_en-US_38.0build1_funsize_signing_task"
            funsize_artifact = get_task_by_name(self.graph, buildername)

            required_elements = (
                "--partial-version 38.0",
                "--locale en-US",
                "--taskid {}".format(funsize_artifact['taskId']),
                "--platform {}".format(buildbot2ftp(platform)),
                "--version 42.0b2",
            )

        # Command requirements for macosx64
        elif platform == 'macosx64':
            buildername = "macosx64_en-US_37.0build2_funsize_signing_task"
            funsize_artifact = get_task_by_name(self.graph, buildername)

            required_elements = (
                "--partial-version 37.0",
                "--locale en-US",
                "--taskid {}".format(funsize_artifact['taskId']),
                "--platform {}".format(buildbot2ftp(platform)),
                "--version 42.0b2",
            )

        @truth
        def verify_command_requirements(task):
            command = ''.join(task['task']['payload']['command'])
            for element in required_elements:
                if element not in command:
                    return False
            else:
                return True

        return verify_command_requirements

    def test_tasks(self):
        for platform, task in self.tasks.iteritems():
            verify(task, self.task_schema, self.generate_command_requirements_validator(platform), TestBeetmoverEnUSPartialsCandidates.not_allowed)


class TestBeetmoverl10nPartialsCandidates(unittest.TestCase, BaseTestBeetmoverCandidates):
    maxDiff = 30000
    graph = None
    # we will end up with one task for each platform
    tasks = None
    l10n_config = {
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
    }

    def setUp(self):
        self.task_schema = Schema({
            'task': {
                'provisionerId': 'aws-provisioner-v1',
                'workerType': 'gecko-3-b-linux',
            }
        }, extra=True, required=True)

        test_kwargs = create_firefox_test_args({
            'updates_enabled': True,
            'push_to_candidates_enabled': True,
            'en_US_config': EN_US_CONFIG,
            'l10n_config': self.l10n_config,
            'branch': 'mozilla-beta',
            'repo_path': 'releases/mozilla-beta',
            'signing_pvt_key': PVT_KEY_FILE,
            'accepted_mar_channel_id': 'firefox-mozilla-beta',
            'signing_cert': 'dep',
            'moz_disable_mar_cert_verification': True,
            'final_verify_channels': ['beta'],
            'release_channels': ['beta']
        })

        self.graph = make_task_graph(**test_kwargs)
        self.tasks = {
            'win32': get_task_by_name(
                self.graph, "release-{}_{}_{}_l10n_repack_partial_{}build{}_beetmover_candidates_{}".format(
                    "mozilla-beta", "firefox", 'win32', "38.0", 1, 1
                )
            ),
            'macosx64': get_task_by_name(
                self.graph, "release-{}_{}_{}_l10n_repack_partial_{}build{}_beetmover_candidates_{}".format(
                    "mozilla-beta", "firefox", 'macosx64', "37.0", 2, 1
                )
            ),
        }

    def generate_command_requirements_validator(self, platform):
        if platform == 'win32':
            buildername = "release-mozilla-beta_firefox_win32_l10n_repack_1_38.0_signing_task"
            funsize_artifact = get_task_by_name(self.graph, buildername)

            required_elements = (
                "--partial-version 38.0",
                "--locale de --locale en-GB --locale zh-TW",
                "--taskid {}".format(funsize_artifact['taskId']),
                "--platform {}".format(buildbot2ftp(platform)),
                "--version 42.0b2",
            )

        elif platform == 'macosx64':
            buildername = "release-mozilla-beta_firefox_macosx64_l10n_repack_1_37.0_signing_task"
            funsize_artifact = get_task_by_name(self.graph, buildername)

            required_elements = (
                "--partial-version 37.0",
                "--locale de --locale en-GB --locale zh-TW",
                "--taskid {}".format(funsize_artifact['taskId']),
                "--platform {}".format(buildbot2ftp(platform)),
                "--version 42.0b2",
            )

        @truth
        def validate_command_requirements(task):
            command = ''.join(task['task']['payload']['command'])
            for element in required_elements:
                if element not in command:
                    return False
            else:
                return True

        return validate_command_requirements

    def test_tasks(self):
        for platform, task in self.tasks.iteritems():
            verify(task, self.task_schema, self.generate_command_requirements_validator(platform), TestBeetmoverl10nPartialsCandidates.not_allowed)
