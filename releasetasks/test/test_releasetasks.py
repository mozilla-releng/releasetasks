# -*- coding: utf-8 -*-
import unittest

from jose import jwt, jws
from jose.constants import ALGORITHMS

from releasetasks.test import do_common_assertions, PVT_KEY_FILE, get_task_by_name, \
    make_task_graph
from releasetasks.util import sign_task
from . import PVT_KEY, PUB_KEY, OTHER_PUB_KEY


class TestTaskSigning(unittest.TestCase):

    def test_task_id(self):
        token = sign_task("xyz", pvt_key=PVT_KEY)
        claims = jwt.decode(token, PUB_KEY, algorithms=[ALGORITHMS.RS512])
        assert claims["taskId"] == "xyz"

    def test_exp(self):
        token = sign_task("xyz", pvt_key=PVT_KEY)
        claims = jwt.decode(token, PUB_KEY, algorithms=[ALGORITHMS.RS512])
        assert "exp" in claims

    def test_exp_int(self):
        token = sign_task("xyz", pvt_key=PVT_KEY)
        claims = jwt.decode(token, PUB_KEY, algorithms=[ALGORITHMS.RS512])
        assert isinstance(claims["exp"], int)

    def test_verify(self):
        token = sign_task("xyz", pvt_key=PVT_KEY)
        claims = jws.verify(token, PUB_KEY, algorithms=[ALGORITHMS.RS512])
        assert claims["taskId"] == "xyz"

    def test_verify_bad_signature(self):
        token = sign_task("xyz", pvt_key=PVT_KEY)
        self.assertRaises(jws.JWSError, jws.verify, token, OTHER_PUB_KEY,
                          [ALGORITHMS.RS512])


class TestMakeGraph(unittest.TestCase):
    """Because of how huge the graph gets, verifying every character of it is
    impossible to maintain. Instead, we verify aspects of it. Eg, making sure
    the correct number of funsize partials are happening, rather than verifying
    the entire funsize tasks."""
    maxDiff = 30000
    graph = None
    task_def = None
    task = None
    payload = None

    def test_funsize_en_US_deps(self):
        graph = make_task_graph(
            version="42.0b2",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            updates_enabled=True,
            bouncer_enabled=False,
            en_US_config={"platforms": {
                "macosx64": {"task_id": "xyz"},
                "win32": {"task_id": "xyy"}
            }},
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

        do_common_assertions(graph)

        for p in ("win32", "macosx64"):
            for v, appV in (("38.0build1", "38.0"), ("37.0build2", "37.0")):
                generator = get_task_by_name(graph, "{}_en-US_{}_funsize_update_generator".format(p, v))
                signing = get_task_by_name(graph, "{}_en-US_{}_funsize_signing_task".format(p, v))
                balrog = get_task_by_name(graph, "{}_en-US_{}_funsize_balrog_task".format(p, v))

                self.assertIsNone(generator.get("requires"))
                self.assertEqual(signing.get("requires"), [generator["taskId"]])
                self.assertEqual(balrog.get("requires"), [signing["taskId"]])
                if p == "win32":
                    self.assertEqual(
                        "http://download.mozilla.org/?product=firefox-%s-complete&os=win&lang=en-US" % appV,
                        generator["task"]["extra"]["funsize"]["partials"][0]["from_mar"])
                    self.assertEqual(
                        "https://queue.taskcluster.net/v1/task/xyy/artifacts/public/build/firefox-42.0.en-US.win32.complete.mar",
                        generator["task"]["extra"]["funsize"]["partials"][0]["to_mar"])
                elif p == "macosx64":
                    self.assertEqual(
                        "http://download.mozilla.org/?product=firefox-%s-complete&os=osx&lang=en-US" % appV,
                        generator["task"]["extra"]["funsize"]["partials"][0]["from_mar"])
                    self.assertEqual(
                        "https://queue.taskcluster.net/v1/task/xyz/artifacts/public/build/firefox-42.0.en-US.mac.complete.mar",
                        generator["task"]["extra"]["funsize"]["partials"][0]["to_mar"])

    def test_funsize_en_US_scopes(self):
        graph = make_task_graph(
            version="42.0b2",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            updates_enabled=True,
            bouncer_enabled=False,
            en_US_config={"platforms": {
                "macosx64": {"task_id": "xyz"},
                "win32": {"task_id": "xyy"}
            }},
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
            product="firefox",
            revision="abcdef123456",
            balrog_api_root="https://fake.balrog/api",
            signing_class="release-signing",
            verifyConfigs={},
            signing_pvt_key=PVT_KEY_FILE,
        )

        do_common_assertions(graph)
        expected_scopes = set([
            "queue:*", "docker-worker:*", "scheduler:*",
            "signing:format:gpg", "signing:format:mar",
            "signing:cert:release-signing",
            "docker-worker:feature:balrogVPNProxy"
        ])
        self.assertTrue(expected_scopes.issubset(graph["scopes"]))

        for p in ("win32", "macosx64"):
            for v in ("38.0build1", "37.0build2"):
                generator = get_task_by_name(graph, "{}_en-US_{}_funsize_update_generator".format(p, v))
                signing = get_task_by_name(graph, "{}_en-US_{}_funsize_signing_task".format(p, v))
                balrog = get_task_by_name(graph, "{}_en-US_{}_funsize_balrog_task".format(p, v))

                self.assertIsNone(generator["task"].get("scopes"))
                self.assertItemsEqual(signing["task"]["scopes"], ["signing:cert:release-signing", "signing:format:mar", "signing:format:gpg"])
                self.assertItemsEqual(balrog["task"]["scopes"], ["docker-worker:feature:balrogVPNProxy"])

    def test_funsize_en_US_scopes_dep_signing(self):
        graph = make_task_graph(
            version="42.0b2",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            updates_enabled=True,
            bouncer_enabled=False,
            en_US_config={"platforms": {
                "macosx64": {"task_id": "xyz"},
                "win32": {"task_id": "xyy"}
            }},
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
            product="firefox",
            revision="abcdef123456",
            balrog_api_root="https://fake.balrog/api",
            signing_class="dep-signing",
            release_channels=["beta"],
            signing_pvt_key=PVT_KEY_FILE,
        )

        do_common_assertions(graph)
        expected_scopes = set([
            "queue:*", "docker-worker:*", "scheduler:*",
            "signing:format:gpg", "signing:format:mar",
            "signing:cert:dep-signing",
        ])
        self.assertTrue(expected_scopes.issubset(graph["scopes"]))
        self.assertNotIn("docker-worker:feature:balrogVPNProxy", graph["scopes"])

        for p in ("win32", "macosx64"):
            for v in ("38.0build1", "37.0build2"):
                generator = get_task_by_name(graph, "{}_en-US_{}_funsize_update_generator".format(p, v))
                signing = get_task_by_name(graph, "{}_en-US_{}_funsize_signing_task".format(p, v))
                balrog = get_task_by_name(graph, "{}_en-US_{}_funsize_balrog_task".format(p, v))

                self.assertIsNone(generator["task"].get("scopes"))
                self.assertItemsEqual(signing["task"]["scopes"], ["signing:cert:dep-signing", "signing:format:mar", "signing:format:gpg"])
                self.assertIsNone(balrog["task"].get("scopes"))
                self.assertEqual(
                    signing["task"]["payload"]["signingManifest"],
                    "https://queue.taskcluster.net/v1/task/%s/artifacts/public/env/manifest.json" % generator["taskId"])

    def test_l10n_one_chunk(self):
        graph = make_task_graph(
            version="42.0b2",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            updates_enabled=False,
            bouncer_enabled=False,
            enUS_platforms=["win32"],
            en_US_config={"platforms": {
                "win32": {"task_id": "xyy"}
            }},
            l10n_config={
                "platforms": {
                    "win32": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.exe",
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
            partial_updates={
                "38.0": {
                    "buildNumber": 1,
                },
                "37.0": {
                    "buildNumber": 2,
                },
            },
            balrog_api_root="https://fake.balrog/api",
            signing_class="release-signing",
            branch="mozilla-beta",
            product="firefox",
            repo_path="releases/mozilla-beta",
            revision="abcdef123456",
            release_channels=["beta"],
            signing_pvt_key=PVT_KEY_FILE,
        )

        do_common_assertions(graph)

        task = get_task_by_name(graph, "release-mozilla-beta_firefox_win32_l10n_repack_1")

        payload = task["task"]["payload"]
        properties = payload["properties"]

        self.assertEqual(task["task"]["provisionerId"], "buildbot-bridge")
        self.assertEqual(task["task"]["workerType"], "buildbot-bridge")
        self.assertEqual(payload["buildername"], "release-mozilla-beta_firefox_win32_l10n_repack")
        self.assertEqual(properties["locales"], "de:default en-GB:default zh-TW:default")
        self.assertEqual(properties["en_us_binary_url"], "https://queue.taskcluster.net/something/firefox.exe")

        # Make sure only one chunk was generated
        self.assertIsNone(get_task_by_name(graph, "release-mozilla-beta_firefox_win32_l10n_repack_0"))
        self.assertIsNone(get_task_by_name(graph, "release-mozilla-beta_firefox_win32_l10n_repack_2"))

        # make sure artifacts task is present
        self.assertIsNotNone(get_task_by_name(graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_1"))
        self.assertIsNone(get_task_by_name(graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_0"))
        self.assertIsNone(get_task_by_name(graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_2"))
        art_task = get_task_by_name(graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_1")
        self.assertEqual(art_task["task"]["provisionerId"], "null-provisioner")
        self.assertEqual(art_task["task"]["workerType"], "buildbot")

    def test_l10n_multiple_chunks(self):
        graph = make_task_graph(
            version="42.0b2",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            updates_enabled=False,
            bouncer_enabled=False,
            enUS_platforms=["win32"],
            en_US_config={"platforms": {
                "win32": {"task_id": "xyy"}
            }},
            l10n_config={
                "platforms": {
                    "win32": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.exe",
                        "locales": ["de", "en-GB", "ru", "uk", "zh-TW"],
                        "chunks": 2,
                    },
                },
                "changesets": {
                    "de": "default",
                    "en-GB": "default",
                    "ru": "default",
                    "uk": "default",
                    "zh-TW": "default",
                },
            },
            partial_updates={
                "38.0": {
                    "buildNumber": 1,
                },
                "37.0": {
                    "buildNumber": 2,
                },
            },
            signing_class="release-signing",
            balrog_api_root="https://fake.balrog/api",
            branch="mozilla-beta",
            product="firefox",
            repo_path="releases/mozilla-beta",
            revision="abcdef123456",
            release_channels=["beta"],
            signing_pvt_key=PVT_KEY_FILE,
        )

        do_common_assertions(graph)

        chunk1 = get_task_by_name(graph, "release-mozilla-beta_firefox_win32_l10n_repack_1")
        chunk2 = get_task_by_name(graph, "release-mozilla-beta_firefox_win32_l10n_repack_2")

        chunk1_properties = chunk1["task"]["payload"]["properties"]
        chunk2_properties = chunk2["task"]["payload"]["properties"]

        self.assertEqual(chunk1["task"]["payload"]["buildername"], "release-mozilla-beta_firefox_win32_l10n_repack")
        self.assertEqual(chunk1_properties["locales"], "de:default en-GB:default ru:default")
        self.assertEqual(chunk1_properties["en_us_binary_url"], "https://queue.taskcluster.net/something/firefox.exe")
        self.assertEqual(chunk2["task"]["payload"]["buildername"], "release-mozilla-beta_firefox_win32_l10n_repack")
        self.assertEqual(chunk2_properties["locales"], "uk:default zh-TW:default")
        self.assertEqual(chunk2_properties["en_us_binary_url"], "https://queue.taskcluster.net/something/firefox.exe")

        self.assertIsNone(get_task_by_name(graph, "release-mozilla-beta_firefox_win32_l10n_repack_3"))

        # make sure artifacts tasks are present
        self.assertIsNotNone(get_task_by_name(graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_1"))
        self.assertIsNotNone(get_task_by_name(graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_2"))
        self.assertIsNone(get_task_by_name(graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_3"))
        # partials
        self.assertIsNotNone(get_task_by_name(graph, "release-mozilla-beta_firefox_win32_l10n_repack_1_37.0_update_generator"))

    def test_encryption(self):
        graph = make_task_graph(
            version="42.0b2",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            updates_enabled=True,
            bouncer_enabled=False,
            en_US_config={"platforms": {
                "macosx64": {"task_id": "xyz"},
                "win32": {"task_id": "xyy"}
            }},
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
            product="firefox",
            revision="abcdef123456",
            balrog_api_root="https://fake.balrog/api",
            signing_class="dep-signing",
            release_channels=["beta"],
            signing_pvt_key=PVT_KEY_FILE,
        )
        do_common_assertions(graph)
        for p in ("win32", "macosx64"):
            for v in ("38.0build1", "37.0build2"):
                balrog = get_task_by_name(graph, "{}_en-US_{}_funsize_balrog_task".format(p, v))
                self.assertEqual(len(balrog["task"]["payload"]["encryptedEnv"]), 2)
                self.assertTrue(
                    balrog["task"]["payload"]["encryptedEnv"][0].startswith("wcB"),
                    "Encrypted string should always start with 'wcB'")

    def test_final_verify_task_definition(self):
        graph = make_task_graph(
            version="42.0b2",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            en_US_config={"platforms": {
                "linux": {"task_id": "xyz"},
                "win32": {"task_id": "xyy"}
            }},
            l10n_config={},
            repo_path="releases/foo",
            revision="fedcba654321",
            branch="foo",
            updates_enabled=False,
            bouncer_enabled=False,
            product="firefox",
            signing_class="release-signing",
            release_channels=["foo"],
            enUS_platforms=["linux", "linux64", "win64", "win32", "macosx64"],
            signing_pvt_key=PVT_KEY_FILE,
        )
        do_common_assertions(graph)

        task_def = get_task_by_name(graph, "foo_final_verify")
        task = task_def["task"]
        payload = task["payload"]
        self.assertEqual(task["provisionerId"], "aws-provisioner-v1")
        self.assertEqual(task["workerType"], "b2gtest")
        self.assertFalse("scopes" in task)
        # XXX: Change the image name once it's in-tree.
        self.assertTrue(payload["image"].startswith("rail/python-test-runner"))
        self.assertFalse("cache" in payload)
        self.assertFalse("artifacts" in payload)
        self.assertTrue("env" in payload)
        self.assertTrue("command" in payload)

        expected_graph_scopes = set([
            "queue:task-priority:high",
        ])
        self.assertTrue(expected_graph_scopes.issubset(graph["scopes"]))

    def test_bouncer_submission_task_definition(self):
        graph = make_task_graph(
            version="42.0b2",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            l10n_config={},
            repo_path="releases/foo",
            product="firefox",
            revision="fedcba654321",
            partial_updates={
                "38.0": {
                    "buildNumber": 1,
                },
                "37.0": {
                    "buildNumber": 2,
                },
            },
            branch="foo",
            updates_enabled=False,
            bouncer_enabled=True,
            signing_class="release-signing",
            release_channels=["foo"],
            enUS_platforms=["linux", "linux64", "win64", "win32", "macosx64"],
            signing_pvt_key=PVT_KEY_FILE,
        )
        do_common_assertions(graph)

        task = get_task_by_name(graph, "release-foo_firefox_bncr_sub")

        payload = task["task"]["payload"]

        self.assertEqual(task["task"]["provisionerId"], "buildbot-bridge")
        self.assertEqual(task["task"]["workerType"], "buildbot-bridge")
        self.assertFalse("scopes" in task)
        # XXX: Change the image name once it's in-tree.
        self.assertEqual(payload["properties"]["partial_versions"], "37.0, 38.0,")
        self.assertEqual(payload["properties"]["build_number"], 3)

        expected_graph_scopes = set([
            "queue:task-priority:high",
        ])
        self.assertTrue(expected_graph_scopes.issubset(graph["scopes"]))

    def test_multi_channel_final_verify_task_definition(self):
        graph = make_task_graph(
            version="42.0b2",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=False,
            en_US_config={"platforms": {
                "linux": {"task_id": "xyz"},
                "win32": {"task_id": "xyy"}
            }},
            l10n_config={},
            repo_path="releases/foo",
            revision="fedcba654321",
            branch="foo",
            updates_enabled=False,
            bouncer_enabled=False,
            product="firefox",
            signing_class="release-signing",
            release_channels=["beta", "release"],
            enUS_platforms=["linux", "linux64", "win64", "win32", "macosx64"],
            signing_pvt_key=PVT_KEY_FILE,
        )
        do_common_assertions(graph)

        for chan in ["beta", "release"]:
            task_def = get_task_by_name(graph,
                                        "{chan}_final_verify".format(chan=chan))
            task = task_def["task"]
            payload = task["payload"]
            self.assertEqual(task["provisionerId"], "aws-provisioner-v1")
            self.assertEqual(task["workerType"], "b2gtest")
            self.assertFalse("scopes" in task)
            # XXX: Change the image name once it's in-tree.
            self.assertTrue(payload["image"].startswith("rail/python-test-runner"))
            self.assertFalse("cache" in payload)
            self.assertFalse("artifacts" in payload)
            self.assertTrue("env" in payload)
            self.assertTrue("command" in payload)

            expected_graph_scopes = set([
                "queue:task-priority:high",
            ])
            self.assertTrue(expected_graph_scopes.issubset(graph["scopes"]))
