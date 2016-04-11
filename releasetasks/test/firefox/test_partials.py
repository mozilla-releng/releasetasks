import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name
from releasetasks.test import PVT_KEY_FILE


class TestEnUSPartials(unittest.TestCase):
    graph = None

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
            push_to_candidates_enabled=False,
            push_to_releases_enabled=False,
            postrelease_version_bump_enabled=False,
            postrelease_bouncer_aliases_enabled=False,
            en_US_config={"platforms": {
                "macosx64": {"task_id": "xyz"},
                "win32": {"task_id": "xyy"}
            }},
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
            release_channels=["beta"],
            final_verify_channels=["beta"],
            signing_pvt_key=PVT_KEY_FILE,
            build_tools_repo_path='build/tools',
        )

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_mar_urls(self):
        for p in ("win32", "macosx64"):
            for v, appV in (("38.0build1", "38.0"), ("37.0build2", "37.0")):
                generator = get_task_by_name(self.graph, "{}_en-US_{}_funsize_update_generator".format(p, v))
                signing = get_task_by_name(self.graph, "{}_en-US_{}_funsize_signing_task".format(p, v))
                balrog = get_task_by_name(self.graph, "{}_en-US_{}_funsize_balrog_task".format(p, v))

                assert generator.get("requires") is None
                assert signing.get("requires") == [generator["taskId"]]
                assert balrog.get("requires") == [signing["taskId"]]
                if p == "win32":
                    assert generator["task"]["extra"]["funsize"]["partials"][0]["from_mar"] == \
                        "http://download.mozilla.org/?product=firefox-%s-complete&os=win&lang=en-US" % appV
                    assert generator["task"]["extra"]["funsize"]["partials"][0]["to_mar"] == \
                        "https://queue.taskcluster.net/v1/task/xyy/artifacts/public/build/firefox-42.0.en-US.win32.complete.mar"
                elif p == "macosx64":
                    assert generator["task"]["extra"]["funsize"]["partials"][0]["from_mar"] == \
                        "http://download.mozilla.org/?product=firefox-%s-complete&os=osx&lang=en-US" % appV
                    assert generator["task"]["extra"]["funsize"]["partials"][0]["to_mar"] == \
                        "https://queue.taskcluster.net/v1/task/xyz/artifacts/public/build/firefox-42.0.en-US.mac.complete.mar"

    def test_funsize_en_US_scopes(self):
        expected_scopes = set([
            "queue:*", "docker-worker:*", "scheduler:*",
            "project:releng:signing:format:gpg", "project:releng:signing:format:mar",
            "project:releng:signing:cert:release-signing",
            "docker-worker:feature:balrogVPNProxy"
        ])
        self.assertTrue(expected_scopes.issubset(self.graph["scopes"]))

    def test_task_scopes(self):
        for p in ("win32", "macosx64"):
            for v in ("38.0build1", "37.0build2"):
                generator = get_task_by_name(self.graph, "{}_en-US_{}_funsize_update_generator".format(p, v))
                signing = get_task_by_name(self.graph, "{}_en-US_{}_funsize_signing_task".format(p, v))
                balrog = get_task_by_name(self.graph, "{}_en-US_{}_funsize_balrog_task".format(p, v))

                self.assertIsNone(generator["task"].get("scopes"))
                self.assertItemsEqual(
                    signing["task"]["scopes"],
                    ["project:releng:signing:cert:release-signing",
                     "project:releng:signing:format:mar",
                     "project:releng:signing:format:gpg"])
                self.assertItemsEqual(balrog["task"]["scopes"], ["docker-worker:feature:balrogVPNProxy"])

    def test_funsize_en_US_scopes_dep_signing(self):
        expected_scopes = set([
            "queue:*", "docker-worker:*", "scheduler:*",
            "project:releng:signing:format:gpg", "project:releng:signing:format:mar",
            "project:releng:signing:cert:release-signing",
        ])
        self.assertTrue(expected_scopes.issubset(self.graph["scopes"]))

    def test_balrog_vpn(self):
        self.assertIn("docker-worker:feature:balrogVPNProxy", self.graph["scopes"])

    def test_signing_manifests(self):
        for p in ("win32", "macosx64"):
            for v in ("38.0build1", "37.0build2"):
                generator = get_task_by_name(self.graph, "{}_en-US_{}_funsize_update_generator".format(p, v))
                signing = get_task_by_name(self.graph, "{}_en-US_{}_funsize_signing_task".format(p, v))
                balrog = get_task_by_name(self.graph, "{}_en-US_{}_funsize_balrog_task".format(p, v))

                self.assertIsNone(generator["task"].get("scopes"))
                self.assertItemsEqual(signing["task"]["scopes"],
                                      ["project:releng:signing:cert:release-signing",
                                       "project:releng:signing:format:mar",
                                       "project:releng:signing:format:gpg"])
                self.assertIsNotNone(balrog["task"].get("scopes"))
                self.assertEqual(
                    signing["task"]["payload"]["signingManifest"],
                    "https://queue.taskcluster.net/v1/task/%s/artifacts/public/env/manifest.json" % generator["taskId"])
