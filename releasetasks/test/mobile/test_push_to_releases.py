import unittest

from releasetasks.test.mobile import (make_task_graph, do_common_assertions,
                                      get_task_by_name, create_fennec_test_args)
from releasetasks.test import generate_scope_validator, PVT_KEY_FILE, verify
from voluptuous import Schema, truth

EN_US_CONFIG = {
    "platforms": {
        "android-4-0-armv7-api15": {"task_id": "xyz"},
        "android-4-2-x86": {"task_id": "xyz"}
    }
}


L10N_CONFIG = {
    "platforms": {
        "android-4-0-armv7-api15": {
            "en_us_binary_url": "https://queue.taskcluster.net/something/fennec.apk",
            "locales": ["de", "en-GB", "zh-TW"],
            "chunks": 1,
        },
        "android-4-2-x86": {
            "en_us_binary_url": "https://queue.taskcluster.net/something/fennec.apk",
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
    human_task_name = "release-{}-{}_push_to_releases_human_decision".format("mozilla-beta",
                                                                             "fennec")

    def setUp(self):
        self.graph_schema = Schema({
            'scopes': generate_scope_validator(scopes={
                "queue:task-priority:high",
                "queue:define-task:aws-provisioner-v1/gecko-3-b-linux",
                "queue:create-task:aws-provisioner-v1/gecko-3-b-linux",
            })
        }, required=True, extra=True)

        self.task_schema = Schema({
            'task': {
                'provisionerId': 'aws-provisioner-v1',
                'workerType': 'gecko-3-b-linux',
            }
        }, extra=True, required=True)

        self.human_task_schema = Schema({
            'task': {
                'provisionerId': 'null-provisioner',
                'workerType': 'human-decision',
            }
        }, extra=True, required=True)

        test_kwargs = create_fennec_test_args({
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
            'eme_free_repacks_platforms': ['win32', 'macosx64'],
            'sha1_repacks_platforms': ['win32'],
            'en_US_config': EN_US_CONFIG,
            'l10n_config': L10N_CONFIG,
        })
        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(
            self.graph, "release-{}-{}_push_to_releases".format("mozilla-beta", "fennec")
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
        requires = []
        requires.append(get_task_by_name(self.graph, "release-mozilla-beta-fennec_chcksms")["taskId"])

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
    human_task_name = "release-{}-{}_push_to_releases_human_decision".format("mozilla-beta",
                                                                             "fennec")

    def setUp(self):
        self.graph_schema = Schema({
            'scopes': generate_scope_validator(scopes={
                "queue:task-priority:high",
                "queue:define-task:aws-provisioner-v1/gecko-3-b-linux",
                "queue:create-task:aws-provisioner-v1/gecko-3-b-linux",
            })
        }, extra=True, required=True)

        self.task_schema = Schema({
            'task': {
                'provisionerId': 'aws-provisioner-v1',
                'workerType': 'gecko-3-b-linux',
            }
        }, extra=True, required=True)

        self.human_task_schema = Schema(None)

        test_kwargs = create_fennec_test_args({
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
            'eme_free_repacks_platforms': ['win32', 'macosx64'],
            'sha1_repacks_platforms': ['win32'],
            'en_US_config': EN_US_CONFIG,
            'l10n_config': L10N_CONFIG,
        })

        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(self.graph, "release-{}-{}_push_to_releases".format("mozilla-beta", "fennec"))
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

    # Returns validator for task dependencies
    def generate_task_requires_validator(self):
        requires = []
        requires.append(get_task_by_name(self.graph, "release-mozilla-beta-fennec_chcksms")["taskId"])

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
    human_task_name = "release-{}-{}_push_to_releases_human_decision".format("mozilla-beta",
                                                                             "fennec")

    def setUp(self):
        test_kwargs = create_fennec_test_args({
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
            'eme_free_repacks_platforms': [],
            'sha1_repacks_platforms': [],
            'en_US_config': EN_US_CONFIG,
            'l10n_config': L10N_CONFIG,
        })

        self.graph = make_task_graph(**test_kwargs)
        self.task = get_task_by_name(self.graph, "release-{}-{}_push_to_releases".format("mozilla-beta", "fennec"))

    @staticmethod
    @truth
    def validate_command(task):
        command = ''.join(task['task']['payload']['command'])
        return "--exclude '.*-EME-free/.*'" not in command and "--exclude '.*/win32-sha1/.*'" not in command

    def test_task(self):
        verify(self.task, TestPushToMirrorsGraph2.validate_command)
