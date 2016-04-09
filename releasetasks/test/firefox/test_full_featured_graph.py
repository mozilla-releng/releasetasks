import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions
from releasetasks.test import PVT_KEY_FILE


class TestFullGraph(unittest.TestCase):
    maxDiff = 30000
    graph = None

    def setUp(self):
        self.graph = make_task_graph(
            product="firefox",
            version="42.0b2",
            next_version="42.0b3",
            appVersion="42.0",
            buildNumber=3,
            source_enabled=True,
            checksums_enabled=True,
            en_US_config={
                "platforms": {
                    "macosx64": {"task_id": "abc"},
                    "win32": {"task_id": "def"},
                    "win64": {"task_id": "jgh"},
                    "linux": {"task_id": "ijk"},
                    "linux64": {"task_id": "lmn"},
                }
            },
            l10n_config={},
            repo_path="releases/foo",
            revision="fedcba654321",
            mozharness_changeset="abcd",
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
            branch="foo",
            updates_enabled=True,
            bouncer_enabled=True,
            push_to_candidates_enabled=True,
            beetmover_candidates_bucket='mozilla-releng-beet-mover-dev',
            push_to_releases_enabled=True,
            postrelease_version_bump_enabled=True,
            postrelease_bouncer_aliases_enabled=True,
            tuxedo_server_url="https://bouncer.real.allizom.org/api",
            signing_class="release-signing",
            verifyConfigs={},
            release_channels=["foo"],
            balrog_api_root="https://balrog.real/api",
            funsize_balrog_api_root="http://balrog/api",
            signing_pvt_key=PVT_KEY_FILE,
            build_tools_repo_path='build/tools',
            push_to_releases_automatic=True,
            partner_repacks_platforms=["win32", "macosx64"],
        )

    def test_common_assertions(self):
        do_common_assertions(self.graph)
