import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args
from releasetasks.test import PVT_KEY_FILE


L10N_CONFIG = {
    'platforms': {
        'win32': {
            'en_us_binary_url': 'https://queue.taskcluster.net/something/firefox.exe',
            'locales': ['de', 'en-GB', 'zh-TW'],
            'chunks': 1
        },
        'win64': {
            'en_us_binary_url': 'https://queue.taskcluster.net/something/firefox.exe',
            'locales': ['de', 'en-GB', 'zh-TW'],
            'chunks': 1
        },
        'macosx64': {
            'en_us_binary_url': 'https://queue.taskcluster.net/something/firefox.exe',
            'locales': ['de', 'en-GB', 'zh-TW'],
            'chunks': 1
        },
    },
    'changesets': {
        'de': 'default',
        'en-GB': 'default',
        'zh-TW': 'default',
    }
}

EN_US_CONFIG = {
    'platforms': {
        'macosx64': {
            'task_id': 'xyz'
        },
        'win32': {
            'task_id': 'xyz'
        },
        'win64': {
            'task_id': 'xyz'
        }
    }
}


class TestBB_UpdateVerify(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    payload = None

    def setUp(self):
        test_args = create_firefox_test_args({
            'updates_enabled': True,
            'push_to_candidates_enabled': True,
            'update_verify_enabled': True,
            'updates_builder_enabled': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'branch': 'beta',
            'release_channels': ['beta'],
            'final_verify_channels': ['beta'],
            'l10n_config': L10N_CONFIG,
            'en_US_config': EN_US_CONFIG,
        })
        self.graph = make_task_graph(**test_args)
        self.task = get_task_by_name(self.graph, "release-beta_firefox_win32_update_verify_beta_3")
        self.payload = self.task["task"]["payload"]
        self.properties = self.payload["properties"]

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_provisioner(self):
        self.assertEqual(self.task["task"]["provisionerId"], "buildbot-bridge")

    def test_worker_type(self):
        self.assertEqual(self.task["task"]["workerType"], "buildbot-bridge")

    def test_scopes_present(self):
        self.assertFalse("scopes" in self.task)

    def test_graph_scopes(self):
        expected_graph_scopes = set([
            "queue:task-priority:high",
        ])
        self.assertTrue(expected_graph_scopes.issubset(self.graph["scopes"]))

    def test_required_property(self):
        self.assertEqual(self.payload['properties']['NO_BBCONFIG'], "1")
        self.assertEqual(self.payload['properties']['VERIFY_CONFIG'],
                         "beta-firefox-win32.cfg")

    def test_chunking_info(self):
        self.assertEqual(self.payload['properties']['TOTAL_CHUNKS'], "12")
        self.assertEqual(self.payload['properties']['THIS_CHUNK'], "3")

    def test_all_builders_exist(self):
        for p in ['win32', 'win64', 'macosx64']:
            for i in range(1, 7):  # test full chunk size
                self.assertIsNotNone(
                    get_task_by_name(
                        self.graph,
                        "release-beta_firefox_%s_update_verify_beta_%s" % (p, i)
                    )
                )

    def test_requires(self):
        en_US_tmpl = "release-beta_firefox_{}_complete_en-US_beetmover_candidates"
        en_US_partials_tmpl = "release-beta_firefox_{p}_partial_en-US_{v}build{n}_beetmover_candidates"
        l10n_tmpl = "release-beta_firefox_{}_l10n_repack_beetmover_candidates_1"
        l10n_partials_tmpl = "release-beta_firefox_{p}_l10n_repack_partial_{v}build{n}_beetmover_candidates_1"
        en_US_balrog_tmpl = "{p}_en-US_{v}build{n}_funsize_balrog_task"
        l10n_balrog_tmpl = "release-beta_firefox_{p}_l10n_repack_1_{v}_balrog_task"

        requires = []
        for completes in (en_US_tmpl, l10n_tmpl):
            requires.extend([
                get_task_by_name(self.graph, completes.format(p))["taskId"]
                for p in ("macosx64", "win32", "win64")
            ])
        for partials in (en_US_partials_tmpl, l10n_partials_tmpl, en_US_balrog_tmpl, l10n_balrog_tmpl):
            requires.extend([
                get_task_by_name(self.graph, partials.format(p=platform, v=p_version, n=p_build_num))["taskId"]
                for platform in ("macosx64", "win32", "win64")
                for p_version, p_build_num in (('38.0', '1'), ('37.0', '2'))
            ])
        requires.append(get_task_by_name(self.graph, "release-beta-firefox_updates")["taskId"])
        self.assertEqual(sorted(self.task["requires"]), sorted(requires))


class TestBB_UpdateVerifyMultiChannel(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    payload = None

    def setUp(self):
        test_kwargs = create_firefox_test_args({
            'updates_enabled': True,
            'push_to_candidates_enabled': True,
            'update_verify_enabled': True,
            'branch': 'beta',
            'release_channels': ["beta", "release"],
            'enUS_platforms': ["linux", "linux64", "win64", "win32", "macosx64"],
            'signing_pvt_key': PVT_KEY_FILE,
            'en_US_config': EN_US_CONFIG,
            'l10n_config': L10N_CONFIG,
        })
        self.graph = make_task_graph(**test_kwargs)

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_multichannel(self):
        for chan in ["beta", "release"]:
            task = get_task_by_name(
                self.graph, "release-beta_firefox_win32_update_verify_{chan}_3".format(chan=chan)
            )
            self.assertEqual(task["task"]["provisionerId"], "buildbot-bridge")
            self.assertEqual(task["task"]["workerType"], "buildbot-bridge")
            self.assertFalse("scopes" in task)
            self.assertEqual(task["task"]["payload"]['properties']['VERIFY_CONFIG'],
                             "{chan}-firefox-win32.cfg".format(chan=chan))
