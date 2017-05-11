import unittest

from releasetasks.test.desktop import make_task_graph, get_task_by_name, \
    do_common_assertions
from releasetasks.test import PVT_KEY_FILE, verify
from releasetasks.test.desktop import create_firefox_test_args
from voluptuous import Schema, truth


class TestL10NSingleChunk(unittest.TestCase):
    maxDiff = 30000
    graph = None
    task = None
    payload = None
    properties = None

    def setUp(self):
        self.chunk_0_schema = self.chunk_2_schema = Schema(None)
        self.chunk_1_schema = Schema({
            'task': {
                'provisionerId': 'buildbot-bridge',
                'workerType': 'buildbot-bridge',
                'payload': {
                    'buildername': 'release-mozilla-beta_firefox_win32_l10n_repack',
                    'properties': {
                        'repo_path': 'releases/mozilla-beta',
                        'script_repo_revision': 'abcd',
                        'locales': 'de:default en-GB:default zh-TW:default',
                        'en_us_binary_url': 'https://queue.taskcluster.net/something/firefox.exe',
                        "mar_tools_url": "https://queue.taskcluster.net/something/",
                    }
                }
            }
        }, extra=True, required=True)

        self.artifact_0_schema = self.artifact_2_schema = Schema(None)
        self.artifact_1_schema = Schema({
            'task': {
                'provisionerId': 'null-provisioner',
                'workerType': 'buildbot',
            }
        }, extra=True, required=True)

        test_arguments = create_firefox_test_args({
            'updates_enabled': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'branch': "mozilla-beta",
            'repo_path': "releases/mozilla-beta",
            'release_channels': ["beta"],
            'final_verify_channels': ["beta"],
            'accepted_mar_channel_id': 'firefox-mozilla-beta',
            'signing_cert': 'dep',
            'moz_disable_mar_cert_verification': True,

            'en_US_config': {
                "platforms": {
                    "win32": {'signed_task_id': 'abc', 'unsigned_task_id': 'abc'}
                }
            },
            'l10n_config': {
                "platforms": {
                    "win32": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.exe",
                        "mar_tools_url": "https://queue.taskcluster.net/something/",
                        "locales": ["de", "en-GB", "zh-TW"],
                        "chunks": 1,
                    },
                    "linux64": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.tar.xz",
                        "mar_tools_url": "https://queue.taskcluster.net/something/",
                        "locales": ["de", "en-GB", "zh-TW"],
                        "chunks": 1,
                    },

                },
                "changesets": {
                    "de": "default",
                    "en-GB": "default",
                    "zh-TW": "default",
                }
            },
        })

        self.graph = make_task_graph(**test_arguments)

        self.chunk_0 = get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_0")
        self.chunk_1 = get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_1")
        self.chunk_2 = get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_2")

        self.artifact_0 = get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_0")
        self.artifact_1 = get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_1")
        self.artifact_2 = get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_2")

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_chunk_0(self):
        verify(self.chunk_0, self.chunk_0_schema)

    def test_chunk_1(self):
        verify(self.chunk_1, self.chunk_1_schema)

    def test_chunk_2(self):
        verify(self.chunk_2, self.chunk_2_schema)

    def test_artifact_0(self):
        verify(self.artifact_0, self.artifact_0_schema)

    def test_artifact_1(self):
        verify(self.artifact_1, self.artifact_1_schema)

    def test_artifact_2(self):
        verify(self.artifact_2, self.artifact_2_schema)

    def test_partials_present(self):
        for pl in ["win32", "linux64"]:
            for part in ["37.0", "38.0"]:
                task_name = "release-mozilla-beta_firefox_{pl}_l10n_repack_1_{part}_update_generator".format(pl=pl, part=part)
                partial_task = get_task_by_name(self.graph, task_name)

                verify(partial_task, Schema(dict))  # The task must exist as a dict (ie not None)

    def test_funsize_name(self):
        for platform in ("win32", "linux64",):
            for version in ("37.0", "38.0",):
                generator_schema = Schema({
                    'task': {'metadata': {'name': "[funsize] Update generating task %s chunk %s for %s" % (platform, "1", version,)}}
                }, extra=True, required=True)
                signing_schema = Schema({
                    'task': {'metadata': {'name': "[funsize] MAR signing task %s chunk %s for %s" % (platform, "1", version,)}}
                }, extra=True, required=True)
                balrog_schema = Schema({
                    'task': {'metadata': {'name':  "[funsize] Publish to Balrog %s chunk %s for %s" % (platform, "1", version,)}}
                }, extra=True, required=True)

                generator_task = get_task_by_name(self.graph,
                                                  "release-mozilla-beta_firefox_{pl}_l10n_repack_1_{part}_update_generator".format(pl=platform, part=version))
                signing_task = get_task_by_name(self.graph,
                                                "release-mozilla-beta_firefox_{pl}_l10n_repack_1_{part}_signing_task".format(pl=platform, part=version))
                balrog_task = get_task_by_name(self.graph,
                                               "release-mozilla-beta_firefox_{pl}_l10n_repack_1_{part}_balrog_task".format(pl=platform, part=version))

                verify(generator_task, generator_schema)
                verify(signing_task, signing_schema)
                verify(balrog_task, balrog_schema)


class TestL10NMultipleChunks(unittest.TestCase):
    maxDiff = 30000
    graph = None
    chunk1 = None
    chunk2 = None
    chunk1_properties = None
    chunk2_properties = None

    def setUp(self):
        self.chunk_1_schema = Schema({
            'task': {
                'payload': {
                    'buildername': 'release-mozilla-beta_firefox_win32_l10n_repack',
                    'properties': {
                        'locales': 'de:default en-GB:default ru:default',
                        'en_us_binary_url': 'https://queue.taskcluster.net/something/firefox.exe',
                        "mar_tools_url": "https://queue.taskcluster.net/something/",
                        'repo_path': 'releases/mozilla-beta',
                        'script_repo_revision': 'abcd',
                    }
                }
            }
        }, extra=True, required=True)

        self.chunk_2_schema = Schema({
            'task': {
                'payload': {
                    'buildername': 'release-mozilla-beta_firefox_win32_l10n_repack',
                    'properties': {
                        'en_us_binary_url': 'https://queue.taskcluster.net/something/firefox.exe',
                        "mar_tools_url": "https://queue.taskcluster.net/something/",
                        'script_repo_revision': 'abcd',
                        'repo_path': 'releases/mozilla-beta',
                        'locales': 'uk:default zh-TW:default',
                    }
                }
            }
        }, extra=True, required=True)

        self.artifacts_1_schema = self.artifacts_2_schema = Schema(dict)  # Tasks must exist as a dict
        self.chunk_3_schema = self.artifacts_3_schema = Schema(None)  # Tasks must be None

        self.partials_schema = Schema(dict)

        test_kwargs = create_firefox_test_args({
            'updates_enabled': True,
            'repo_path': 'releases/mozilla-beta',
            'branch': 'mozilla-beta',
            'signing_pvt_key': PVT_KEY_FILE,
            'release_channels': ['beta'],
            'final_verify_channels': ['beta'],
            'accepted_mar_channel_id': 'firefox-mozilla-beta',
            'signing_cert': 'dep',
            'moz_disable_mar_cert_verification': True,
            'en_US_platforms': ['win32'],
            'en_US_config': {
                "platforms": {
                    "win32": {'signed_task_id': 'abc', 'unsigned_task_id': 'abc'}
                }
            },
            'l10n_config': {
                "platforms": {
                    "win32": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.exe",
                        "mar_tools_url": "https://queue.taskcluster.net/something/",
                        "locales": ["de", "en-GB", "ru", "uk", "zh-TW"],
                        "chunks": 2,
                    },
                    "linux64": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.tar.xz",
                        "mar_tools_url": "https://queue.taskcluster.net/something/",
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
        })
        self.graph = make_task_graph(**test_kwargs)

        self.chunk_1 = get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_1")
        self.chunk_2 = get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_2")
        self.chunk_3 = get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_3")

        self.artifacts_1 = get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_1")
        self.artifacts_2 = get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_2")
        self.artifacts_3 = get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_artifacts_3")

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_chunk_1(self):
        verify(self.chunk_1, self.chunk_1_schema)

    def test_chunk_2(self):
        verify(self.chunk_2, self.chunk_2_schema)

    def test_chunk_3(self):
        verify(self.chunk_3, self.chunk_3_schema)

    def test_artifacts_1(self):
        verify(self.artifacts_1, self.artifacts_1_schema)

    def test_artifacts_2(self):
        verify(self.artifacts_2, self.artifacts_2_schema)

    def test_artifacts_3(self):
        verify(self.artifacts_3, self.artifacts_3_schema)

    def test_partials_present(self):
        for pl in ["win32", "linux64"]:
            for part in ["37.0", "38.0"]:
                for chunk in [1, 2]:
                    partials_name_1 = "release-mozilla-beta_firefox_{pl}_l10n_repack_{chunk}_{part}_update_generator".format(
                        pl=pl, part=part, chunk=chunk)
                    partials_name_2 = "release-mozilla-beta_firefox_{pl}_l10n_repack_{chunk}_{part}_signing_task".format(
                        pl=pl, part=part, chunk=chunk)

                    partials_1 = get_task_by_name(self.graph, partials_name_1)
                    partials_2 = get_task_by_name(self.graph, partials_name_2)

                    # Verify the partial tasks are not none
                    verify(partials_1, self.partials_schema)
                    verify(partials_2, self.partials_schema)

    def test_funsize_name(self):
        for platform in ("win32", "linux64",):
            for version in ("37.0", "38.0",):
                for chunk in ('1', '2',):
                    generator_schema = Schema({
                        'task': {'metadata': {
                            'name': "[funsize] Update generating task %s chunk %s for %s" % (platform, chunk, version,)}}
                    }, extra=True, required=True)
                    signing_schema = Schema({
                        'task': {'metadata': {
                            'name': "[funsize] MAR signing task %s chunk %s for %s" % (platform, chunk, version,)}}
                    }, extra=True, required=True)
                    balrog_schema = Schema({
                        'task': {'metadata': {
                            'name': "[funsize] Publish to Balrog %s chunk %s for %s" % (platform, chunk, version,)}}
                    }, extra=True, required=True)
                    generator = get_task_by_name(self.graph,
                                                 "release-mozilla-beta_firefox_{pl}_l10n_repack_{c}_{part}_update_generator".format(
                                                     pl=platform, part=version, c=chunk))
                    signing = get_task_by_name(self.graph,
                                               "release-mozilla-beta_firefox_{pl}_l10n_repack_{c}_{part}_signing_task".format(
                                                   pl=platform, part=version, c=chunk))
                    balrog = get_task_by_name(self.graph,
                                              "release-mozilla-beta_firefox_{pl}_l10n_repack_{c}_{part}_balrog_task".format(
                                                  pl=platform, part=version, c=chunk))

                    verify(generator, generator_schema)
                    verify(signing, signing_schema)
                    verify(balrog, balrog_schema)


class TestL10NNewLocales(unittest.TestCase):
    maxDiff = 30000
    graph = None

    def setUp(self):
        test_kwargs = create_firefox_test_args({
            'updates_enabled': True,
            'push_to_candidates_enabled': True,
            'branch': 'mozilla-beta',
            'repo_path': 'releases/mozilla-beta',
            'signing_pvt_key': PVT_KEY_FILE,
            'release_channels': ['beta'],
            'final_verify_channels': ['beta'],
            'accepted_mar_channel_id': 'firefox-mozilla-beta',
            'signing_cert': 'dep',
            'moz_disable_mar_cert_verification': True,
            'enUS_platforms': ['win32'],
            'en_US_config': {
                "platforms": {
                    "win32": {'signed_task_id': 'abc', 'unsigned_task_id': 'abc'}
                }
            },
            'l10n_config': {
                "platforms": {
                    "win32": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.exe",
                        "mar_tools_url": "https://queue.taskcluster.net/something/",
                        "locales": ["de", "en-GB", "ru", "uk", "zh-TW"],
                        "chunks": 1,
                    },
                    "linux64": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.tar.xz",
                        "mar_tools_url": "https://queue.taskcluster.net/something/",
                        "locales": ["de", "en-GB", "ru", "uk", "zh-TW"],
                        "chunks": 1,
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
            'partial_updates': {
                '38.0': {
                    'buildNumber': 1,
                    'locales': [
                        'de', 'en-GB', 'ru', 'uk', 'zh-TW'
                    ]
                },
                '37.0': {
                    'buildNumber': 2,
                    'locales': [
                        'de', 'en-GB', 'ru', 'uk'
                    ]
                }
            }
        })
        self.graph = make_task_graph(**test_kwargs)

        self.update_generator_37 = get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_1_37.0_update_generator")
        self.update_generator_38 = get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_1_38.0_update_generator")

        self.beetmover_candidates_37 = get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_partial_37.0build2_beetmover_candidates_1")
        self.beetmover_candidates_38 = get_task_by_name(self.graph, "release-mozilla-beta_firefox_win32_l10n_repack_partial_38.0build1_beetmover_candidates_1")

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    @staticmethod
    @truth
    def verify_new_locale_not_in_update_generator(task):
        partials = task["task"]["extra"]["funsize"]["partials"]
        return sorted(["de", "en-GB", "ru", "uk"]) == sorted([p["locale"] for p in partials])

    @staticmethod
    @truth
    def verify_new_locale_in_update_generator(task):
        partials = task["task"]["extra"]["funsize"]["partials"]
        return sorted(["de", "en-GB", "ru", "uk", "zh-TW"]) == sorted([p["locale"] for p in partials])

    @staticmethod
    @truth
    def verify_new_locale_not_in_beetmover(task):
        command = " ".join(task["task"]["payload"]["command"])
        return "--locale zh-TW" not in command and "--locale en-GB" in command

    @staticmethod
    @truth
    def verify_new_locale_in_beetmover(task):
        command = " ".join(task["task"]["payload"]["command"])
        return "--locale zh-TW" in command and "--locale en-GB" in command

    def test_update_generator_37(self):
        verify(self.update_generator_37, TestL10NNewLocales.verify_new_locale_not_in_update_generator)

    def test_update_generator_38(self):
        verify(self.update_generator_38, TestL10NNewLocales.verify_new_locale_in_update_generator)

    def test_beetmover_37(self):
        verify(self.beetmover_candidates_37, TestL10NNewLocales.verify_new_locale_not_in_beetmover)

    def test_beetmover_38(self):
        verify(self.beetmover_candidates_38, TestL10NNewLocales.verify_new_locale_in_beetmover)
