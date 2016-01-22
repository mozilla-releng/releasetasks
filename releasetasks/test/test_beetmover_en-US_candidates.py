import unittest

from releasetasks.test import make_task_graph, PVT_KEY_FILE, \
    do_common_assertions, get_task_by_name


class TestBeetmoverEnUSCandidates(unittest.TestCase):
    maxDiff = 30000
    graph = None
    # we will end up with one task for each platform
    tasks = None
    en_US_config = {
        "platforms": {
            "macosx64": {"task_id": "xyz", "upload_platform": "mac"},
            "win32": {"task_id": "xyy", "upload_platform": "win32"}
        }
    }

    def setUp(self):
        self.graph = make_task_graph(
            version="42.0b2",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            updates_enabled=True,
            bouncer_enabled=False,
            push_to_candidates_enabled=True,
            postrelease_version_bump_enabled=True,
            en_US_config=self.en_US_config,
            l10n_config={},
            enUS_platforms=["win32", "macosx64"],
            partial_updates={
                "38.0": {
                    "buildNumber": 1,
                },
                "37.0": {
                    "buildNumber": 2,
                },
            },
            branch="mozilla-beta",
            repo_path="releases/mozilla-beta",
            product="firefox",
            revision="abcdef123456",
            balrog_api_root="https://fake.balrog/api",
            signing_class="release-signing",
            verifyConfigs={},
            signing_pvt_key=PVT_KEY_FILE,
        )
        self.tasks = {
            'win32': get_task_by_name(
                self.graph, "release-{}_{}_{}_en-US_beetmover_candidates".format("mozilla-beta",
                                                                                 "firefox",
                                                                                 'win32')
            ),
            'macosx64': get_task_by_name(
                self.graph, "release-{}_{}_{}_en-US_beetmover_candidates".format("mozilla-beta",
                                                                                 "firefox",
                                                                                 'macosx64')
            ),
        }

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

    def test_platform_in_command(self):
        for platform, task in self.tasks.iteritems():
            upload_platform = self.en_US_config['platforms'][platform]['upload_platform']
            command = task['task']['payload']['command']
            self.assertTrue("--platform {}".format(upload_platform) in "".join(command))

    def test_version_in_command(self):
        for platform, task in self.tasks.iteritems():
            command = task['task']['payload']['command']
            self.assertTrue("--version 42.0b2" in "".join(command))
            self.assertTrue("--locale en-US" in "".join(command))

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

    def test_graph_scopes(self):
        expected_graph_scopes = set([
            "queue:task-priority:high",
            "queue:define-task:aws-provisioner-v1/opt-linux64",
            "queue:create-task:aws-provisioner-v1/opt-linux64"
        ])
        self.assertTrue(expected_graph_scopes.issubset(self.graph["scopes"]))
