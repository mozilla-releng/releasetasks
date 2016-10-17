import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args, scope_check_factory
from releasetasks.test import PVT_KEY_FILE
from releasetasks.util import buildbot2ftp
from voluptuous import Schema
from voluptuous.humanize import validate_with_humanized_errors


EN_US_CONFIG = {
    "platforms": {
        "macosx64": {"task_id": "xyz"},
        "win32": {"task_id": "xyy"}
    }
}


class BaseTestBeetmoverCandidates(object):

    GRAPH_SCHEMA = Schema({
        'scopes': scope_check_factory(scopes={
            'queue:task-priority:high',
            'queue:define-task:aws-provisioner-v1/opt-linux64',
            'queue:create-task:aws-provisioner-v1/opt-linux64',
        })
    }, extra=True, required=True)

    BASE_SCHEMA = Schema({
        'task': {
            'provisionerId': 'aws-provisioner-v1',
            'workerType': 'opt-linux64',
        }
    }, extra=True, required=True)

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_scopes_present(self):
        for platform, task in self.tasks.iteritems():
            self.assertFalse("scopes" in task)

    def test_platform_in_command(self):
        for platform, task in self.tasks.iteritems():
            command = task['task']['payload']['command']
            self.assertTrue("--platform {}".format(buildbot2ftp(platform)) in "".join(command))

    def test_version_in_command(self):
        for platform, task in self.tasks.iteritems():
            command = task['task']['payload']['command']
            self.assertTrue("--version 42.0b2" in "".join(command))


class TestBeetmoverEnUSCandidates(unittest.TestCase, BaseTestBeetmoverCandidates):
    maxDiff = 30000
    graph = None
    # we will end up with one task for each platform
    tasks = None

    def setUp(self):
        test_kwargs = create_firefox_test_args({
            'push_to_candidates_enabled': True,
            'en_US_config': EN_US_CONFIG,
            'branch': "mozilla-beta",
            'repo_path': "releases/mozilla-beta",
            'signing_pvt_key': PVT_KEY_FILE,
            'build_tools_repo_path': 'build/tools',
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

    def test_app_version_in_command(self):
        for platform, task in self.tasks.iteritems():
            command = task['task']['payload']['command']
            self.assertTrue("--app-version 42.0" in "".join(command))

    def test_locale_in_command(self):
        for platform, task in self.tasks.iteritems():
            command = task['task']['payload']['command']
            self.assertTrue("--locale en-US" in "".join(command))

    def test_taskid_in_command(self):
        for platform, task in self.tasks.iteritems():
            en_US_taskid = EN_US_CONFIG['platforms'][platform]['task_id']
            command = task['task']['payload']['command']
            self.assertTrue("--taskid {}".format(en_US_taskid) in "".join(command))

    def test_bucket_in_command(self):
        for platform, task in self.tasks.iteritems():
            command = task['task']['payload']['command']
            self.assertTrue("--bucket {}".format("fake_bucket") in "".join(command))

    def test_extra_build_props(self):
        for platform, task in self.tasks.iteritems():
            build_props = task['task']['extra']['build_props']
            self.assertEqual(build_props["product"], "firefox")
            self.assertEqual(build_props["locales"], ["en-US"])
            self.assertEqual(build_props["branch"], "mozilla-beta")
            self.assertTrue("platform" in build_props)
            self.assertEqual(build_props["version"], "42.0b2")
            self.assertEqual(build_props["revision"], "abcdef123456")


class TestBeetmover110nCandidates(unittest.TestCase, BaseTestBeetmoverCandidates):
    maxDiff = 30000
    graph = None
    # we will end up with one task for each platform
    tasks = None
    l10n_config = {
        "platforms": {
            "win32": {
                "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.exe",
                "locales": ["de", "en-GB", "zh-TW"],
                "chunks": 1,
            },
            "macosx64": {
                "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.tar.xz",
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
        test_kwargs = create_firefox_test_args({
            'push_to_candidates_enabled': True,
            'branch': 'mozilla-beta',
            'repo_path': 'releases/mozilla-beta',
            'release_channels': ['beta'],
            'final_verify_channels': ['beta'],
            'signing_pvt_key': PVT_KEY_FILE,
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

    TASK_SCHEMA = Schema({
        'task': {
            'payload': {
                'command': lambda command: '--app-version 42.0' in ''.join(command),
            }
        }
    })

    def test_app_version_in_command(self):
        for platform, task in self.tasks.iteritems():
            command = task['task']['payload']['command']
            self.assertTrue("--app-version 42.0" in "".join(command))

    def test_locale_in_command(self):
        for platform, task in self.tasks.iteritems():
            command = task['task']['payload']['command']
            self.assertTrue("--locale de --locale en-GB --locale zh-TW" in "".join(command))

    def test_bucket_in_command(self):
        for platform, task in self.tasks.iteritems():
            command = task['task']['payload']['command']
            self.assertTrue("--bucket {}".format("fake_bucket") in "".join(command))

    def test_taskid_in_command(self):
        for platform, task in self.tasks.iteritems():
            l10n_artifact_task = get_task_by_name(
                self.graph,
                "release-mozilla-beta_firefox_{}_l10n_repack_artifacts_1".format(platform)
            )
            command = task['task']['payload']['command']
            self.assertTrue("--taskid {}".format(l10n_artifact_task['taskId']) in "".join(command))

    def test_extra_build_props(self):
        for platform, task in self.tasks.iteritems():
            schema = Schema({
                'task': {
                    'extra': {
                        'build_props': {
                            'product': 'firefox',
                            'locales': ["de", "en-GB", "zh-TW"],
                            'branch': 'mozilla-beta',
                            'version': '42.0b2',
                            'revision': 'abcdef123456'
                        }
                    }
                }
            }, extra=True, required=True)
            assert validate_with_humanized_errors(task, schema)
            self.assertTrue("platform" in task['task']['extra']['build_props'])


class TestBeetmoverEnUSPartialsCandidates(unittest.TestCase, BaseTestBeetmoverCandidates):
    maxDiff = 30000
    graph = None
    # we will end up with one task for each platform
    tasks = None

    def setUp(self):
        test_kwargs = create_firefox_test_args({
            'updates_enabled': True,
            'push_to_candidates_enabled': True,
            'branch': 'mozilla-beta',
            'repo_path:': 'mozilla/beta',
            'signing_pvt_key': PVT_KEY_FILE,
            'en_US_config': EN_US_CONFIG,
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

    def test_partial_version_in_command(self):
        for platform, task in self.tasks.iteritems():
            command = task['task']['payload']['command']
            if platform == "win32":
                self.assertTrue("--partial-version 38.0" in "".join(command))
            else:  # macosx64
                self.assertTrue("--partial-version 37.0" in "".join(command))

    def test_locale_in_command(self):
        for platform, task in self.tasks.iteritems():
            command = task['task']['payload']['command']
            self.assertTrue("--locale en-US" in "".join(command))

    def test_taskid_in_command(self):
        for platform, task in self.tasks.iteritems():
            if platform == "win32":
                buildername = "win32_en-US_38.0build1_funsize_signing_task"
            else:  # macosx64
                buildername = "macosx64_en-US_37.0build2_funsize_signing_task"
            funsize_artifact = get_task_by_name(self.graph, buildername)
            command = task['task']['payload']['command']
            self.assertTrue("--taskid {}".format(funsize_artifact['taskId']) in "".join(command))


class TestBeetmoverl10nPartialsCandidates(unittest.TestCase, BaseTestBeetmoverCandidates):
    maxDiff = 30000
    graph = None
    # we will end up with one task for each platform
    tasks = None
    l10n_config = {
        "platforms": {
            "win32": {
                "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.exe",
                "locales": ["de", "en-GB", "zh-TW"],
                "chunks": 1,
            },
            "macosx64": {
                "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.tar.xz",
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
        test_kwargs = create_firefox_test_args({
            'updates_enabled': True,
            'push_to_candidates_enabled': True,
            'en_US_config': EN_US_CONFIG,
            'l10n_config': self.l10n_config,
            'branch': 'mozilla-beta',
            'repo_path': 'releases/mozilla-beta',
            'signing_pvt_key': PVT_KEY_FILE,
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

    def test_partial_version_in_command(self):
        for platform, task in self.tasks.iteritems():
            command = task['task']['payload']['command']
            if platform == "win32":
                self.assertTrue("--partial-version 38.0" in "".join(command))
            else:  # macosx64
                self.assertTrue("--partial-version 37.0" in "".join(command))

    def test_locale_in_command(self):
        for platform, task in self.tasks.iteritems():
            command = task['task']['payload']['command']
            self.assertTrue("--locale de --locale en-GB --locale zh-TW" in "".join(command))

    def test_taskid_in_command(self):
        for platform, task in self.tasks.iteritems():
            if platform == "win32":
                buildername = "release-mozilla-beta_firefox_win32_l10n_repack_1_38.0_signing_task"
            else:  # macosx64
                buildername = "release-mozilla-beta_firefox_macosx64_l10n_repack_1_37.0_signing_task"
            funsize_artifact = get_task_by_name(self.graph, buildername)
            command = task['task']['payload']['command']
            self.assertTrue("--taskid {}".format(funsize_artifact['taskId']) in "".join(command))
