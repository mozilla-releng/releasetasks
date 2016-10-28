import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args
from releasetasks.test import generate_scope_validator, PVT_KEY_FILE, verify
from voluptuous import Schema, truth


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
        self.graph_schema = Schema({
            'scopes': generate_scope_validator(scopes={'queue:task-priority:high'}),
        }, extra=True, required=True)

        self.task_schema = Schema({
            'task': {
                'provisionerId': 'buildbot-bridge',
                'workerType': 'buildbot-bridge',
                'payload': {
                    'properties': {
                        'NO_BBCONFIG': '1',
                        'VERIFY_CONFIG': 'beta-firefox-win32.cfg',
                        'TOTAL_CHUNKS': '12',
                        'THIS_CHUNK': '3'
                    }
                }
            }
        }, extra=True, required=True)

        # Ensure the task exists, and is a dict
        self.builder_exists_schema = Schema(dict)

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

    def generate_task_dependency_validator(self):
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

        @truth
        def validate_task_dependencies(task):
            return sorted(requires) == sorted(task['requires'])

        return validate_task_dependencies

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_bb_update_verify_task(self):
        verify(self.task, self.task_schema, self.generate_task_dependency_validator())

    def test_bb_update_verify_graph(self):
        verify(self.graph, self.graph_schema)

    def test_all_builders_exist(self):
        for p in ['win32', 'win64', 'macosx64']:
            for i in xrange(1, 7):  # test full chunk size
                builder_task = get_task_by_name(self.graph, "release-beta_firefox_%s_update_verify_beta_%s" % (p, i))
                verify(builder_task, self.builder_exists_schema)


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

    @staticmethod
    @truth
    def not_allowed(task):
        return "scopes" not in task

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_multichannel(self):
        for chan in ["beta", "release"]:
            multichan_schema = Schema({
                'task': {
                    'provisionerId': 'buildbot-bridge',
                    'workerType': 'buildbot-bridge',
                    'payload': {
                        'properties': {
                            'VERIFY_CONFIG': "{chan}-firefox-win32.cfg".format(chan=chan),
                        }
                    }
                }
            }, extra=True, required=True)

            multichan_task = get_task_by_name(self.graph, "release-beta_firefox_win32_update_verify_{chan}_3".format(chan=chan))
            verify(multichan_task, multichan_schema, TestBB_UpdateVerifyMultiChannel.not_allowed)
