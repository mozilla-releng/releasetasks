import unittest

from releasetasks.test.desktop import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args
from releasetasks.test import generate_scope_validator, PVT_KEY_FILE, verify
from voluptuous import Schema, truth


class TestEnUSPartials(unittest.TestCase):
    graph = None

    def setUp(self):
        self.graph_schema = Schema({
            'scopes': generate_scope_validator(scopes={
                "queue:*",
                "docker-worker:*",
                "scheduler:*",
                "project:releng:signing:format:gpg",
                "project:releng:signing:format:mar",
                "project:releng:signing:cert:release-signing",
                "docker-worker:feature:balrogVPNProxy"
            })
        }, extra=True, required=True)

        test_kwargs = create_firefox_test_args({
            'updates_enabled': True,
            'branch': 'mozilla-beta',
            'repo_path': 'releases/mozilla-beta',
            'signing_pvt_key': PVT_KEY_FILE,
            'release_channels': ['beta'],
            'final_verify_channels': ['beta'],
            'accepted_mar_channel_id': 'firefox-mozilla-beta',
            'signing_cert': 'dep',
            'moz_disable_mar_cert_verification': True,
            'en_US_config': {
                "platforms": {
                    "macosx64": {"unsigned_task_id": "xyz", "signed_task_id": "xyz"},
                    "win32": {"unsigned_task_id": "xyy", "signed_task_id": "xyy"},
                }
            },
        })
        self.graph = make_task_graph(**test_kwargs)
        self.generator_image = get_task_by_name(self.graph, "funsize_update_generator_image")
        self.funsize_balrog_image = get_task_by_name(self.graph, "funsize_balrog_image")

    @staticmethod
    @truth
    def generator_not_allowed(task):
        return 'scopes' not in task['task']

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_graph(self):
        verify(self.graph, self.graph_schema)

    def test_generator_signing_balrog_tasks(self):
        for p in ("win32", "macosx64"):
            for v, appV in (("38.0build1", "38.0"), ("37.0build2", "37.0")):
                generator = get_task_by_name(self.graph, "{}_en-US_{}_funsize_update_generator".format(p, v))
                signing = get_task_by_name(self.graph, "{}_en-US_{}_funsize_signing_task".format(p, v))
                balrog = get_task_by_name(self.graph, "{}_en-US_{}_funsize_balrog_task".format(p, v))

                generator_schema = Schema({
                    'requires': [self.generator_image['taskId']],
                    'task': {
                        'metadata': {
                            'name': "[funsize] Update generating task %s %s for %s" % (p, "en-US", v.split('build')[0],)
                        }
                    }
                }, extra=True, required=True)

                signing_schema = Schema({
                    'requires': [generator['taskId']],
                    'task': {
                        'metadata': {
                            'name': "[funsize] MAR signing task %s %s for %s" % (p, "en-US", v.split('build')[0],),
                        },
                        'payload': {
                            'signingManifest': "https://queue.taskcluster.net/v1/task/%s/artifacts/public/env/manifest.json" % generator["taskId"],
                        },
                        'scopes': [
                            "project:releng:signing:cert:release-signing",
                            "project:releng:signing:format:mar",
                            "project:releng:signing:format:gpg",
                        ],
                    },
                }, extra=True, required=True)

                balrog_schema = Schema({
                    'requires': [signing['taskId'], self.funsize_balrog_image['taskId']],
                    'task': {
                        'scopes': ["docker-worker:feature:balrogVPNProxy"],
                        'metadata': {
                            'name': "[funsize] Publish to Balrog %s %s for %s" % (p, "en-US", v.split('build')[0],),
                        }
                    }
                }, extra=True, required=True)

                if p == "win32":
                    generator_schema = generator_schema.extend({
                        'task': {
                            'extra': {
                                'funsize': {
                                    'partials': [
                                        {
                                            'from_mar': "http://download.mozilla.org/?product=firefox-%s-complete&os=win&lang=en-US" % appV,
                                            'to_mar': "https://queue.taskcluster.net/v1/task/xyy/artifacts/public/build/firefox-42.0.en-US.win32.complete.mar",
                                        }
                                    ]
                                }
                            }
                        }
                    })

                elif p == "macosx64":
                    generator_schema = generator_schema.extend({
                        'task': {
                            'extra': {
                                'funsize': {
                                    'partials': [
                                        {
                                            'from_mar': "http://download.mozilla.org/?product=firefox-%s-complete&os=osx&lang=en-US" % appV,
                                            'to_mar': "https://queue.taskcluster.net/v1/task/xyz/artifacts/public/build/firefox-42.0.en-US.mac.complete.mar",
                                        }
                                    ]
                                }
                            }
                        }
                    })

                verify(generator, generator_schema, TestEnUSPartials.generator_not_allowed)
                verify(balrog, balrog_schema)
                verify(signing, signing_schema)
