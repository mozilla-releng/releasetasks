import unittest

from releasetasks.test.desktop import make_tasks, create_firefox_test_args
from releasetasks.test import PVT_KEY_FILE

EN_US_CONFIG = {
    "platforms": {
        "macosx64": {
            "unsigned_task_id": "xyz", "signed_task_id": "xyx",
            "repackage_task_id": "xyx",
            "repackage-signing_task_id": "xyx", "ci_system": "tc"
        },
        "win32": {
            "unsigned_task_id": "xyz", "signed_task_id": "xyx",
            "repackage_task_id": "xyx",
            "repackage-signing_task_id": "xyx", "ci_system": "tc"
        },
        "win64": {
            "unsigned_task_id": "xyz", "signed_task_id": "xyx",
            "repackage_task_id": "xyx",
            "repackage-signing_task_id": "xyx", "ci_system": "tc"
        },
        "linux": {
            "unsigned_task_id": "xyz", "signed_task_id": "xyx",
            "repackage_task_id": "xyx",
            "repackage-signing_task_id": "xyx", "ci_system": "tc"
        },
        "linux64": {
            "unsigned_task_id": "xyz", "signed_task_id": "xyx",
            "repackage_task_id": "xyx",
            "repackage-signing_task_id": "xyx", "ci_system": "tc"
        },
    }
}


l10n_changesets = """ach f26087a6a6fd
af eeac1ca62457
an a4f5fb57979d
ar 2e0b0a82bd19
as ecbc1fafe3fb
ast 0b2ab3ced18d
az d3d47516000e
be 681a9354692e
bg 0ed29af471d6
bn-BD 99d13290e75a
bn-IN cd84ee209b9c
br 28b291423375
bs 18b79a52d6d3
ca 2caa231de0ef
cak 490b329c0c18
cs 61f3b8744fd4
cy d90268690ab1
da e9d1f54f3bff
de 0d34bc2e13ea
dsb ecb136141d45
el 13ee5cd21a66
en-GB 4efed4b7a026
en-ZA 57e2d4c01a4f
eo 79399e61c448
es-AR 1b1828090e64
es-CL 14c2933ac5cb
es-ES fbb0fb506927
es-MX 12ac6da7e878
et 52df77b40a67
eu 3f99a55125ed
fa 45ef3a098c22
ff ce70d79833b7
fi 87e077685a24
fr dd9cdb0516df
fy-NL bc875e89b956
ga-IE 707061b06788
gd f937bddd78eb
gl df4a43546115
gn 504188cb41ff
gu-IN 0e5b275489be
he 0c53c3756f7d
hi-IN f09bb5cf94ff
hr d317c15ea672
hsb 4e2d86fbcc08
hu b75e490cf7de
hy-AM 1cc0c7b53435
id 00395930bb83
is 3a1027971afd
it ff2d53b08a2b
ja d10444a85593
ja-JP-mac 3a8f2188846f
ka d7355ad91eb4
kab c79bbdfb6e57
kk 9bb6a3c31e31
km 3bf31b0b6d9e
kn 085cc4cfccad
ko 2a8956fc58a2
lij 217da84c31d3
lt 1a561e58708f
lv 5bda26d1509c
mai b78d319868ff
mk 26b755e4f87b
ml 818f2d7fc3b1
mr a4338b8b6d14
ms 92b0b0f0e4bd
my a4558a17d4c3
nb-NO d50a43efc007
nl a8f7ad7a0e39
nn-NO e00fbf3066c1
or 11e8e75808ae
pa-IN f01bcb8c13a2
pl 7a50b8205d44
pt-BR 22d3acbbbec4
pt-PT c5e6aee4edc0
rm f16da0c1a769
ro c6acb9eef864
ru 9075bdd2bb8a
si d91975c0b4d8
sk b9a06fade0e6
sl 26af553910a4
son abb58457c998
sq 4374d5e275dd
sr baec6e6f600d
sv-SE bf5faf4c09d4
ta 68b1bc5f3425
te 0e7ca5597a9b
th 4d496dbcb3fd
tr d9f5398e98f8
uk a95815527227
ur 7aaa28d05a00
uz 3a1c7abc05f8
vi acfca579d4ad
xh c2ac7c43e358
zh-CN 954437bef7e7
zh-TW ab71eb9f2d52""".splitlines()

l10n_changesets = dict([line.split(" ") for line in l10n_changesets])

L10N_CONFIG = {
    "platforms": {
        "win32": {
            "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.exe",
            "mar_tools_url": "https://queue.taskcluster.net/something/",
            "locales": l10n_changesets.keys(),
            "chunks": 10,
        },
        "macosx64": {
            "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.tar.xz",
            "mar_tools_url": "https://queue.taskcluster.net/something/",
            "locales": l10n_changesets.keys(),
            "chunks": 10,
        },
        "win64": {
            "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.tar.xz",
            "mar_tools_url": "https://queue.taskcluster.net/something/",
            "locales": l10n_changesets.keys(),
            "chunks": 10,
        },
        "linux64": {
            "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.tar.xz",
            "mar_tools_url": "https://queue.taskcluster.net/something/",
            "locales": l10n_changesets.keys(),
            "chunks": 10,
        },
        "linux": {
            "en_us_binary_url": "https://queue.taskcluster.net/something/firefox.tar.xz",
            "mar_tools_url": "https://queue.taskcluster.net/something/",
            "locales": l10n_changesets.keys(),
            "chunks": 10,
        },
    },
    "changesets": l10n_changesets,
}


class TestPushToMirrorsHuman(unittest.TestCase):
    maxDiff = 30000
    tasks = None

    def setUp(self):
        test_kwargs = create_firefox_test_args({
            'checksums_enabled': True,
            'updates_enabled': True,
            'push_to_candidates_enabled': True,
            'push_to_releases_enabled': True,
            'branch': 'mozilla-beta',
            'repo_path': 'releases/mozilla-beta',
            'signing_pvt_key': PVT_KEY_FILE,
            'accepted_mar_channel_id': 'firefox-mozilla-beta',
            'signing_cert': 'dep',
            'moz_disable_mar_cert_verification': True,
            'release_channels': ['beta', 'release'],
            'final_verify_channels': ['beta', 'release'],
            'partner_repacks_platforms': ['win32', 'macosx64'],
            'eme_free_repacks_platforms': ['win32', 'macosx64'],
            'sha1_repacks_platforms': ['win32'],
            'en_US_config': EN_US_CONFIG,
            'l10n_config': L10N_CONFIG,
            'partial_updates': {
                "38.0": {"buildNumber": 1, "locales": l10n_changesets.keys()},
                "38.0.1": {"buildNumber": 1, "locales": l10n_changesets.keys()},
                "37.0": {"buildNumber": 1, "locales": l10n_changesets.keys()},
                "36.0": {"buildNumber": 1, "locales": l10n_changesets.keys()},
                "35.0": {"buildNumber": 1, "locales": l10n_changesets.keys()},
            },
        })
        self.taskGroupId, self.tasks, _ = make_tasks(**test_kwargs)

    def test_deps(self):
        for task_id, task in self.tasks.iteritems():
            if task_id == self.taskGroupId:
                assert not task.get("dependencies")
            else:
                assert task.get("dependencies")

    def test_dummy(self):
        assert max([len(t.get("dependencies", [])) for t in self.tasks.values()]) <= 100
