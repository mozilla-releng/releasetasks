import unittest

from releasetasks.test.desktop import do_common_assertions, get_task_by_name, \
    make_task_graph, create_firefox_test_args
from releasetasks.test import PVT_KEY_FILE, verify
from voluptuous import Schema, truth


class TestPartnerRepacks(unittest.TestCase):
    maxDiff = 30000
    graph = None
    tasks = None
    partner_tasks = None
    eme_free_tasks = None
    sha1_tasks = None

    def setUp(self):
        # Task attributes common to each partner repack
        common_task_schema = Schema({
            'task': {
                'provisionerId': 'buildbot-bridge',
                'workerType': 'buildbot-bridge',
                'payload': {
                    'properties': {
                        'version': '42.0b2',
                        'build_number': 3,
                    }
                }
            }
        })

        self.partner_task_schema = common_task_schema.extend({
            'task': {
                'payload': {
                    'properties': {
                        'repack_manifests_url': 'git@github.com:mozilla-partners/repack-manifests.git',
                    }
                }
            }
        }, required=True, extra=True)

        self.eme_free_task_schema = common_task_schema.extend({
            'task': {
                'payload': {
                    'properties': {
                        'repack_manifests_url': 'https://github.com/mozilla-partners/mozilla-EME-free-manifest',
                    }
                }
            }
        }, required=True, extra=True)

        self.sha1_task_schema = common_task_schema.extend({
            'task': {
                'payload': {
                    'properties': {
                        'repack_manifests_url': 'https://github.com/mozilla-partners/mozilla-sha1-manifest',
                    }
                }
            }
        }, required=True, extra=True)

        test_kwargs = create_firefox_test_args({
            'push_to_candidates_enabled': True,
            'push_to_releases_enabled': True,
            'push_to_releases_automatic': True,
            'source_enabled': True,
            'signing_pvt_key': PVT_KEY_FILE,
            'partner_repacks_platforms': ['win32', 'linux'],
            'eme_free_repacks_platforms': ['win32', 'macosx64'],
            'sha1_repacks_platforms': ['win32'],
            'release_channels': ['foo', 'bar'],
            'en_US_config': {
                "platforms": {
                    "linux": {'signed_task_id': 'abc', 'unsigned_task_id': 'abc'},
                    "macosx64": {'signed_task_id': 'abc', 'unsigned_task_id': 'abc'},
                    "win32": {'signed_task_id': 'abc', 'unsigned_task_id': 'abc'},
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
                    "linux": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.tar.xz",
                        "mar_tools_url": "https://queue.taskcluster.net/something/",
                        "locales": ["de", "en-GB", "zh-TW"],
                        "chunks": 1,
                    },
                    "macosx64": {
                        "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.dmg",
                        "mar_tools_url": "https://queue.taskcluster.net/something/",
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
        })

        self.graph = make_task_graph(**test_kwargs)
        self.partner_tasks = [
            get_task_by_name(self.graph, "release-foo-firefox-{}_partner_repacks".format(platform))
            for platform in ["win32", "linux"]
        ]
        self.eme_free_tasks = [
            get_task_by_name(self.graph, "release-foo-firefox-{}_eme_free_repacks".format(platform))
            for platform in ["win32", "macosx64"]
        ]
        self.sha1_tasks = [
            get_task_by_name(self.graph, "release-foo-firefox-{}_sha1_repacks".format(platform))
            for platform in ["win32"]
        ]

        self.partner_push_to_mirrors_task = get_task_by_name(self.graph, "release-foo-firefox_partner_repacks_copy_to_releases")
        self.push_to_mirrors_task = get_task_by_name(self.graph, "release-foo_firefox_push_to_releases")

        self.upstream_dependencies = [
            "release-foo_firefox_{}_complete_en-US_beetmover_candidates".format(platform)
            for platform in ["win32", "linux", "macosx64"]
        ] + [
            "release-foo_firefox_{}_l10n_repack_beetmover_candidates_1".format(platform)
            for platform in ["win32", "linux", "macosx64"]
        ]

    # Returns a validator for task dependencies
    def generate_dependency_validator(self):
        requires = [get_task_by_name(self.graph, t)['taskId'] for t in self.upstream_dependencies]

        @truth
        def validate_partner_repack_dependencies(task):
            return sorted(task['requires']) == sorted(requires)

        return validate_partner_repack_dependencies

    # Returns a validator for not required task dependencies
    def generate_not_required_validator(self):
        push_to_mirrors = get_task_by_name(self.graph, "release-foo_firefox_push_to_releases")

        @truth
        def validate_not_required_dependencies(task):
            return task['taskId'] not in push_to_mirrors['requires']

        return validate_not_required_dependencies

    # Returns a validator for partner push to releases dependencies
    def generate_partner_push_to_releases_requires_validator(self):
        repacks_task_ids = [task['taskId'] for task in self.partner_tasks] + \
                           [task['taskId'] for task in self.eme_free_tasks] + \
                           [task['taskId'] for task in self.sha1_tasks]

        requires = repacks_task_ids + [self.push_to_mirrors_task['taskId']]

        @truth
        def validate_partner_push_to_releases_requires(task):
            return sorted(self.partner_push_to_mirrors_task['requires']) == sorted(requires)

        return validate_partner_push_to_releases_requires

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_partner_tasks(self):
        for partner_task in self.partner_tasks:
            verify(partner_task, self.partner_task_schema, self.generate_dependency_validator(), self.generate_not_required_validator())

    def test_eme_free_tasks(self):
        for eme_free_task in self.eme_free_tasks:
            verify(eme_free_task, self.eme_free_task_schema, self.generate_dependency_validator(), self.generate_not_required_validator())

    def test_sha1_tasks(self):
        for sha1_task in self.sha1_tasks:
            verify(sha1_task, self.sha1_task_schema, self.generate_dependency_validator(), self.generate_not_required_validator())

    def test_partner_push_to_releases_task(self):
        verify(self.partner_push_to_mirrors_task, self.generate_partner_push_to_releases_requires_validator())
