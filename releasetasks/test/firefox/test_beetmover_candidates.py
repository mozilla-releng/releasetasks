import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name
from releasetasks.test import PVT_KEY_FILE
from releasetasks.util import buildbot2ftp


class BaseTestBeetmoverCandidates(object):

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_provisioner(self):
        for platform, task in self.tasks.iteritems():
            self.assertEqual(task["task"]["provisionerId"], "aws-provisioner-v1")

    def test_worker_type(self):
        for platform, task in self.tasks.iteritems():
            self.assertEqual(task["task"]["workerType"], "opt-linux64")

    def test_scopes_present(self):
        for platform, task in self.tasks.iteritems():
            self.assertFalse("scopes" in task)

    def test_graph_scopes(self):
        expected_graph_scopes = set([
            "queue:task-priority:high",
            "queue:define-task:aws-provisioner-v1/opt-linux64",
            "queue:create-task:aws-provisioner-v1/opt-linux64"
        ])
        self.assertTrue(expected_graph_scopes.issubset(self.graph["scopes"]))

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
    en_US_config = {
        "platforms": {
            "macosx64": {"task_id": "xyz"},
            "win32": {"task_id": "xyy"}
        }
    }

    def setUp(self):
        self.graph = make_task_graph(
            version="42.0b2",
            next_version="42.0b3",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            checksums_enabled=False,
            updates_enabled=False,
            bouncer_enabled=False,
            push_to_candidates_enabled=True,
            beetmover_candidates_bucket='mozilla-releng-beet-mover-dev',
            push_to_releases_enabled=False,
            uptake_monitoring_enabled=False,
            postrelease_version_bump_enabled=False,
            postrelease_mark_as_shipped_enabled=False,
            postrelease_bouncer_aliases_enabled=False,
            en_US_config=self.en_US_config,
            l10n_config={},
            partial_updates={
                "38.0": {
                    "buildNumber": 1,
                    "locales": ["de", "en-GB", "zh-TW"],
                },
                "37.0": {
                    "buildNumber": 2,
                    "locales": ["de", "en-GB", "zh-TW"],
                },
            },
            branch="mozilla-beta",
            repo_path="releases/mozilla-beta",
            product="firefox",
            revision="abcdef123456",
            mozharness_changeset="abcd",
            balrog_api_root="https://balrog.real/api",
            funsize_balrog_api_root="http://balrog/api",
            signing_class="release-signing",
            verifyConfigs={},
            signing_pvt_key=PVT_KEY_FILE,
            build_tools_repo_path='build/tools',
            publish_to_balrog_channels=None,
        )
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
            en_US_taskid = self.en_US_config['platforms'][platform]['task_id']
            command = task['task']['payload']['command']
            self.assertTrue("--taskid {}".format(en_US_taskid) in "".join(command))

    def test_bucket_in_command(self):
        for platform, task in self.tasks.iteritems():
            command = task['task']['payload']['command']
            self.assertTrue("--bucket {}".format("mozilla-releng-beet-mover-dev") in "".join(command))

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
    en_US_config = {
        "platforms": {
            "macosx64": {"task_id": "xyz"},
            "win32": {"task_id": "xyy"}
        }
    }
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
        self.graph = make_task_graph(
            version="42.0b2",
            next_version="42.0b3",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            checksums_enabled=False,
            updates_enabled=False,
            bouncer_enabled=False,
            push_to_candidates_enabled=True,
            beetmover_candidates_bucket='mozilla-releng-beet-mover-dev',
            push_to_releases_enabled=False,
            uptake_monitoring_enabled=False,
            postrelease_version_bump_enabled=False,
            postrelease_mark_as_shipped_enabled=False,
            postrelease_bouncer_aliases_enabled=False,
            en_US_config=self.en_US_config,
            l10n_config=self.l10n_config,
            partial_updates={
                "38.0": {
                    "buildNumber": 1,
                    "locales": ["de", "en-GB", "zh-TW"],
                },
                "37.0": {
                    "buildNumber": 2,
                    "locales": ["de", "en-GB", "zh-TW"],
                },
            },
            balrog_api_root="https://balrog.real/api",
            funsize_balrog_api_root="http://balrog/api",
            signing_class="release-signing",
            branch="mozilla-beta",
            product="firefox",
            repo_path="releases/mozilla-beta",
            revision="abcdef123456",
            mozharness_changeset="abcd",
            release_channels=["beta"],
            final_verify_channels=["beta"],
            signing_pvt_key=PVT_KEY_FILE,
            build_tools_repo_path='build/tools',
            publish_to_balrog_channels=None,
        )
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
            self.assertTrue("--bucket {}".format("mozilla-releng-beet-mover-dev") in "".join(command))

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
            build_props = task['task']['extra']['build_props']
            self.assertEqual(build_props["product"], "firefox")
            self.assertEqual(build_props["locales"], ["de", "en-GB", "zh-TW"])
            self.assertEqual(build_props["branch"], "mozilla-beta")
            self.assertTrue("platform" in build_props)
            self.assertEqual(build_props["version"], "42.0b2")
            self.assertEqual(build_props["revision"], "abcdef123456")


class TestBeetmoverEnUSPartialsCandidates(unittest.TestCase, BaseTestBeetmoverCandidates):
    maxDiff = 30000
    graph = None
    # we will end up with one task for each platform
    tasks = None
    en_US_config = {
        "platforms": {
            "macosx64": {"task_id": "xyz"},
            "win32": {"task_id": "xyy"}
        }
    }

    def setUp(self):
        self.graph = make_task_graph(
            version="42.0b2",
            next_version="42.0b3",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            checksums_enabled=False,
            updates_enabled=True,
            bouncer_enabled=False,
            push_to_candidates_enabled=True,
            beetmover_candidates_bucket='mozilla-releng-beet-mover-dev',
            push_to_releases_enabled=False,
            uptake_monitoring_enabled=False,
            postrelease_version_bump_enabled=False,
            postrelease_mark_as_shipped_enabled=False,
            postrelease_bouncer_aliases_enabled=False,
            en_US_config=self.en_US_config,
            l10n_config={},
            partial_updates={
                "38.0": {
                    "buildNumber": 1,
                    "locales": ["de", "en-GB", "zh-TW"],
                },
                "37.0": {
                    "buildNumber": 2,
                    "locales": ["de", "en-GB", "zh-TW"],
                },
            },
            branch="mozilla-beta",
            repo_path="releases/mozilla-beta",
            product="firefox",
            revision="abcdef123456",
            mozharness_changeset="abcd",
            balrog_api_root="https://balrog.real/api",
            funsize_balrog_api_root="http://balrog/api",
            signing_class="release-signing",
            verifyConfigs={},
            signing_pvt_key=PVT_KEY_FILE,
            build_tools_repo_path='build/tools',
            publish_to_balrog_channels=None,
        )
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
    en_US_config = {
        "platforms": {
            "macosx64": {"task_id": "xyz"},
            "win32": {"task_id": "xyy"}
        }
    }
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
        self.graph = make_task_graph(
            version="42.0b2",
            next_version="42.0b3",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            checksums_enabled=False,
            updates_enabled=True,
            bouncer_enabled=False,
            push_to_candidates_enabled=True,
            beetmover_candidates_bucket='mozilla-releng-beet-mover-dev',
            push_to_releases_enabled=False,
            uptake_monitoring_enabled=False,
            postrelease_version_bump_enabled=False,
            postrelease_mark_as_shipped_enabled=False,
            postrelease_bouncer_aliases_enabled=False,
            en_US_config=self.en_US_config,
            l10n_config=self.l10n_config,
            partial_updates={
                "38.0": {
                    "buildNumber": 1,
                    "locales": ["de", "en-GB", "zh-TW"],
                },
                "37.0": {
                    "buildNumber": 2,
                    "locales": ["de", "en-GB", "zh-TW"],
                },
            },
            balrog_api_root="https://balrog.real/api",
            funsize_balrog_api_root="http://balrog/api",
            signing_class="release-signing",
            branch="mozilla-beta",
            product="firefox",
            repo_path="releases/mozilla-beta",
            revision="abcdef123456",
            mozharness_changeset="abcd",
            release_channels=["beta"],
            final_verify_channels=["beta"],
            signing_pvt_key=PVT_KEY_FILE,
            build_tools_repo_path='build/tools',
            publish_to_balrog_channels=None,
        )
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
