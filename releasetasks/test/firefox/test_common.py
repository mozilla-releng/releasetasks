import unittest

from jose import jwt, jws
from jose.constants import ALGORITHMS

from releasetasks import sign_task
from releasetasks.test import PVT_KEY_FILE, PVT_KEY, PUB_KEY, OTHER_PUB_KEY
from releasetasks.test.firefox import make_task_graph, do_common_assertions, \
    get_task_by_name, create_firefox_test_args


class TestTaskSigning(unittest.TestCase):

    def test_task_id(self):
        token = sign_task("xyz", pvt_key=PVT_KEY)
        claims = jwt.decode(token, PUB_KEY, algorithms=[ALGORITHMS.RS512])
        assert claims["taskId"] == "xyz"

    def test_exp(self):
        token = sign_task("xyz", pvt_key=PVT_KEY)
        claims = jwt.decode(token, PUB_KEY, algorithms=[ALGORITHMS.RS512])
        assert "exp" in claims

    def test_exp_int(self):
        token = sign_task("xyz", pvt_key=PVT_KEY)
        claims = jwt.decode(token, PUB_KEY, algorithms=[ALGORITHMS.RS512])
        assert isinstance(claims["exp"], int)

    def test_verify(self):
        token = sign_task("xyz", pvt_key=PVT_KEY)
        claims = jws.verify(token, PUB_KEY, algorithms=[ALGORITHMS.RS512])
        assert claims["taskId"] == "xyz"

    def test_verify_bad_signature(self):
        token = sign_task("xyz", pvt_key=PVT_KEY)
        self.assertRaises(jws.JWSError, jws.verify, token, OTHER_PUB_KEY,
                          [ALGORITHMS.RS512])


class TestEncryption(unittest.TestCase):
    maxDiff = 30000

    def test_encryption(self):
        test_kwargs = create_firefox_test_args({
            'updates_enabled': True,
            'repo_path': 'foo/bar',
            'branch': 'mozilla-beta',
            'signing_class': 'dep-signing',
            'release_channels': ['beta'],
            'final_verify_channels': ['beta'],
            'signing_pvt_key': PVT_KEY_FILE,
            'en_US_config': {
                "platforms": {
                    "macosx64": {"task_id": "xyz"},
                    "win32": {"task_id": "xyy"}
                }
            },
        })
        graph = make_task_graph(**test_kwargs)
        do_common_assertions(graph)
        for p in ("win32", "macosx64"):
            for v in ("38.0build1", "37.0build2"):
                balrog = get_task_by_name(graph, "{}_en-US_{}_funsize_balrog_task".format(p, v))
                self.assertEqual(len(balrog["task"]["payload"]["encryptedEnv"]), 2)
                self.assertTrue(
                    balrog["task"]["payload"]["encryptedEnv"][0].startswith("wcB"),
                    "Encrypted string should always start with 'wcB'")


class TestGraphScopes(unittest.TestCase):
    maxDiff = 30000
    graph = None

    def setUp(self):
        test_kwargs = create_firefox_test_args({
            'signing_pvt_key': PVT_KEY_FILE,
            'en_US_config': {
                "platforms": {
                    "linux": {"task_id": "xyz"},
                    "win32": {"task_id": "xyy"}
                }
            },
        })
        self.graph = make_task_graph(**test_kwargs)

    def test_common_assertions(self):
        do_common_assertions(self.graph)

    def test_no_tasks(self):
        self.assertIsNone(self.graph["tasks"])

    def test_scopes(self):
        expected_scopes = set([
            "project:releng:signing:format:gpg",
            "queue:define-task:buildbot-bridge/buildbot-bridge",
            "queue:create-task:buildbot-bridge/buildbot-bridge",
            "queue:task-priority:high",
        ])
        self.assertTrue(expected_scopes.issubset(self.graph["scopes"]))
