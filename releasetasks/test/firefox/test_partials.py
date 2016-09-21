import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name
from releasetasks.test import PVT_KEY_FILE, create_test_args


class TestEnUSPartials(unittest.TestCase):
    graph = None

    def setUp(self):
        test_kwargs = create_test_args({
            'updates_enabled': True,
            'branch': 'mozilla-beta',
            'repo_path': 'releases/mozilla-beta',
            'signing_pvt_key': PVT_KEY_FILE,
            'release_channels': ['beta'],
            'final_verify_channels': ['beta'],
            'en_US_config': {
                "platforms": {
                    "macosx64": {"task_id": "xyz"},
                    "win32": {"task_id": "xyy"}
                }
            },
        })
        self.graph = make_task_graph(**test_kwargs)

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_mar_urls(self):
        generator_image = get_task_by_name(self.graph, "funsize_update_generator_image")
        funsize_balrog_image = get_task_by_name(self.graph, "funsize_balrog_image")
        for p in ("win32", "macosx64"):
            for v, appV in (("38.0build1", "38.0"), ("37.0build2", "37.0")):
                generator = get_task_by_name(self.graph, "{}_en-US_{}_funsize_update_generator".format(p, v))
                signing = get_task_by_name(self.graph, "{}_en-US_{}_funsize_signing_task".format(p, v))
                balrog = get_task_by_name(self.graph, "{}_en-US_{}_funsize_balrog_task".format(p, v))

                assert generator.get("requires") == [generator_image["taskId"]]
                assert signing.get("requires") == [generator["taskId"]]
                assert sorted(balrog.get("requires")) == sorted([signing["taskId"], funsize_balrog_image["taskId"]])
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

    def test_funsize_name(self):
        for p in ("win32", "macosx64",):
            for v in ("38.0build1", "37.0build2",):
                generator = get_task_by_name(self.graph, "{}_en-US_{}_funsize_update_generator".format(p, v))
                signing = get_task_by_name(self.graph, "{}_en-US_{}_funsize_signing_task".format(p, v))
                balrog = get_task_by_name(self.graph, "{}_en-US_{}_funsize_balrog_task".format(p, v))
                self.assertEquals(generator["task"]["metadata"]["name"],
                                  "[funsize] Update generating task %s %s for %s" % (p, "en-US", v.split('build')[0],))
                self.assertEquals(signing["task"]["metadata"]["name"],
                                  "[funsize] MAR signing task %s %s for %s" % (p, "en-US", v.split('build')[0],))
                self.assertEquals(balrog["task"]["metadata"]["name"],
                                  "[funsize] Publish to Balrog %s %s for %s" % (p, "en-US", v.split('build')[0],))
