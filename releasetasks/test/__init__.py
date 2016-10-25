import os
from voluptuous import All, Schema
from voluptuous.humanize import validate_with_humanized_errors


def read_file(path):
    with open(path) as f:
        return f.read()


def verify(data, *validators):
    assert validate_with_humanized_errors(data, Schema(All(*validators)))

PVT_KEY_FILE = os.path.join(os.path.dirname(__file__), "id_rsa")
PVT_KEY = read_file(PVT_KEY_FILE)
PUB_KEY = read_file(os.path.join(os.path.dirname(__file__), "id_rsa.pub"))
OTHER_PUB_KEY = read_file(os.path.join(os.path.dirname(__file__),
                                       "other_rsa.pub"))
DUMMY_PUBLIC_KEY = os.path.join(os.path.dirname(__file__), "public.key")
