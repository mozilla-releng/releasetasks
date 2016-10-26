import unittest

from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args
from releasetasks.test import generate_scope_validator, PVT_KEY_FILE, verify
from voluptuous import Schema, truth

EN_US_CONFIG = {
    "platforms": {
        "macosx64": {"task_id": "xyz"},
        "win32": {"task_id": "xyy"}
    }
}


L10N_CONFIG = {
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


class TestPushToMirrorsHuman(unittest.TestCase):
    maxDiff = 30000
    graph = None
    # we will end up with one task for each platform
    tasks = None
    human_task_name = "release-{}_{}_push_to_releases_human_decision".format("mozilla-beta",
                                                                             "firefox")

    def setUp(self):
        self.graph_schema = Schema({
            'scopes': generate_scope_validator(scopes={
                "queue:task-priority:high",
                "queue:define-task:aws-provisioner-v1/opt-linux64",
                "queue:create-task:aws-provisioner-v1/opt-linux64",
            })
        }, required=True, extra=True)

        self.task_schema = Schema({
            'task': {
                'provisionerId': 'aws-provisioner-v1',
                'workerType': 'opt-linux64',
            }
        }, extra=True, required=True)

        self.human_task_schema = Schema({
            'task': {
                'provisionerId': 'null-provisioner',
                'workerType': 'human-decision',
            }
        }, extra=True, required=True)

        test_kwargs = create_firefox_test_args({
            'checksums_enabled': True,
            'updates_enabled': True,
            'push_to_candidates_enabled': True,
            'push_to_releases_enabled': True,
            'branch': 'mozilla-beta',
            'repo_path': 'releases/mozilla-beta',
            'signing_pvt_key': PVT_KEY_FILE,
            'release_channels': ['beta', 'release'],
            'final_verify_channels': ['beta', 'release'],
            'partner_repacks_platforms': ['win32', 'macosx64'],
            'en_US_config': EN_US_CONFIG,
            'l10n_config': L10N_CONFIG,
        })
        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(
            self.graph, "release-{}_{}_push_to_releases".format("mozilla-beta", "firefox")
        )
        self.human_task = get_task_by_name(self.graph, self.human_task_name)

    @staticmethod
    @truth
    def validate_task_not_allowed(task):
        return 'scopes' not in task['task']

    @staticmethod
    @truth
    def validate_task_command(task):
        command = ''.join(task['task']['payload']['command'])
        return '--version 42.0b2' in command and '--build-number 3' in command

    def generate_task_requires_validator(self):
        requires = [self.human_task['taskId']]

        @truth
        def validate_task_requires(task):
            return requires == task['requires']

        return validate_task_requires

    def generate_human_task_requires_validator(self):
        en_US_tmpl = "release-mozilla-beta_firefox_{}_complete_en-US_beetmover_candidates"
        en_US_partials_tmpl = "release-mozilla-beta_firefox_{}_partial_en-US_{}build{}_beetmover_candidates"
        l10n_tmpl = "release-mozilla-beta_firefox_{}_l10n_repack_beetmover_candidates_1"
        l10n_partials_tmpl = "release-mozilla-beta_firefox_{}_l10n_repack_partial_{}build{}_beetmover_candidates_1"
        requires = []
        for completes in (en_US_tmpl, l10n_tmpl):
            requires.extend([
                                get_task_by_name(self.graph, completes.format(p))["taskId"]
                                for p in ("macosx64", "win32")
                                ])
        for partials in (en_US_partials_tmpl, l10n_partials_tmpl):
            requires.extend([
                                get_task_by_name(self.graph, partials.format(platform, p_version, p_build_num))[
                                    "taskId"]
                                for platform in ("macosx64", "win32")
                                for p_version, p_build_num in (('38.0', '1'), ('37.0', '2'))
                                ])
        requires.append(get_task_by_name(self.graph, "release-mozilla-beta-firefox_chcksms")["taskId"])

        @truth
        def validate_human_task_requires(human_task):
            return sorted(human_task['requires']) == sorted(requires)

        return validate_human_task_requires

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_graph(self):
        verify(self.graph, self.graph_schema)

    def test_task(self):
        verify(self.task, self.task_schema,
               TestPushToMirrorsHuman.validate_task_not_allowed,
               TestPushToMirrorsHuman.validate_task_command,
               self.generate_task_requires_validator())

    def test_human_task(self):
        verify(self.human_task, self.human_task_schema, self.generate_human_task_requires_validator())


class TestPushToMirrorsAutomatic(unittest.TestCase):
    maxDiff = 30000
    graph = None
    # we will end up with one task for each platform
    tasks = None
    human_task_name = "release-{}_{}_push_to_releases_human_decision".format("mozilla-beta",
                                                                             "firefox")

    def setUp(self):
        self.graph_schema = Schema({
            'scopes': generate_scope_validator(scopes={
                "queue:task-priority:high",
                "queue:define-task:aws-provisioner-v1/opt-linux64",
                "queue:create-task:aws-provisioner-v1/opt-linux64",
            })
        }, extra=True, required=True)

        self.task_schema = Schema({
            'task': {
                'provisionerId': 'aws-provisioner-v1',
                'workerType': 'opt-linux64',
            }
        }, extra=True, required=True)

        self.human_task_schema = Schema(None)

        test_kwargs = create_firefox_test_args({
            'checksums_enabled': True,
            'updates_enabled': True,
            'push_to_candidates_enabled': True,
            'push_to_releases_enabled': True,
            'push_to_releases_automatic': True,
            'branch': 'mozilla-beta',
            'repo_path': 'releases/mozilla-beta',
            'signing_pvt_key': PVT_KEY_FILE,
            'release_channels': ['beta', 'release'],
            'final_verify_channels': ['beta', 'release'],
            'partner_repacks_platforms': ['win32', 'macosx64'],
            'en_US_config': EN_US_CONFIG,
            'l10n_config': L10N_CONFIG,
        })

        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(self.graph, "release-{}_{}_push_to_releases".format("mozilla-beta", "firefox"))
        self.human_task = get_task_by_name(self.graph, self.human_task_name)

    @staticmethod
    @truth
    def validate_task_not_allowed(task):
        return 'scopes' not in task['task']

    @staticmethod
    @truth
    def validate_task_command(task):
        command = ''.join(task['task']['payload']['command'])
        return '--version 42.0b2' in command and \
               '--build-number 3' in command and \
               "--exclude '.*-EME-free/.*'" in command and \
               "--exclude '.*/win32-sha1/.*'" in command and \
               "--exclude '.*/snap/.*'" in command

    # Returns validator for task dependencies
    def generate_task_requires_validator(self):
        en_US_tmpl = "release-mozilla-beta_firefox_{}_complete_en-US_beetmover_candidates"
        en_US_partials_tmpl = "release-mozilla-beta_firefox_{}_partial_en-US_{}build{}_beetmover_candidates"
        l10n_tmpl = "release-mozilla-beta_firefox_{}_l10n_repack_beetmover_candidates_1"
        l10n_partials_tmpl = "release-mozilla-beta_firefox_{}_l10n_repack_partial_{}build{}_beetmover_candidates_1"
        requires = []
        for completes in (en_US_tmpl, l10n_tmpl):
            requires.extend([
                get_task_by_name(self.graph, completes.format(p))["taskId"]
                for p in ("macosx64", "win32")
            ])
        for partials in (en_US_partials_tmpl, l10n_partials_tmpl):
            requires.extend([
                get_task_by_name(self.graph, partials.format(platform, p_version, p_build_num))[
                    "taskId"]
                for platform in ("macosx64", "win32")
                for p_version, p_build_num in (('38.0', '1'), ('37.0', '2'))
            ])
        requires.append(get_task_by_name(self.graph, "release-mozilla-beta-firefox_chcksms")["taskId"])

        @truth
        def validate_task_requires(task):
            return sorted(task['requires']) == sorted(requires)

        return validate_task_requires

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_task(self):
        verify(self.task, self.task_schema,
               TestPushToMirrorsAutomatic.validate_task_not_allowed,
               TestPushToMirrorsAutomatic.validate_task_command,
               self.generate_task_requires_validator())

    def test_human_task(self):
        verify(self.human_task, self.human_task_schema)


class TestPushToMirrorsGraph2(unittest.TestCase):
    maxDiff = 30000
    graph = None
    # we will end up with one task for each platform
    tasks = None
    human_task_name = "release-{}_{}_push_to_releases_human_decision".format("mozilla-beta",
                                                                             "firefox")

    def setUp(self):
        test_kwargs = create_firefox_test_args({
            'checksums_enabled': True,
            'updates_enabled': True,
            'push_to_candidates_enabled': True,
            'push_to_releases_enabled': True,
            'push_to_releases_automatic': True,
            'branch': 'mozilla-beta',
            'repo_path': 'releases/mozilla-beta',
            'signing_pvt_key': PVT_KEY_FILE,
            'release_channels': ['beta', 'release'],
            'final_verify_channels': ['beta', 'release'],
            'partner_repacks_platforms': [],
            'en_US_config': EN_US_CONFIG,
            'l10n_config': L10N_CONFIG,
        })

        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(self.graph, "release-{}_{}_push_to_releases".format("mozilla-beta", "firefox"))

    @staticmethod
    @truth
    def validate_command(task):
        command = ''.join(task['task']['payload']['command'])
        return "--exclude '.*-EME-free/.*'" not in command and "--exclude '.*/win32-sha1/.*'" not in command

    def test_task(self):
        verify(self.task, TestPushToMirrorsGraph2.validate_command)
