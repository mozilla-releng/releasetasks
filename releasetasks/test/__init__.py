import os
from voluptuous import All, Schema, truth
from voluptuous.humanize import validate_with_humanized_errors


def read_file(path):
    with open(path) as f:
        return f.read()


#  Assert the validated output is the same as the input
#  Voluptuous will raise an Invalid error if something goes wrong
#  We check equality with the input data in case input data was None, which would fail the test.
def verify(data, *validators):
    assert validate_with_humanized_errors(data, Schema(All(*validators))) == data


def generate_scope_validator(scopes=None):
    @truth
    def validate_scopes(schema_input):
        return scopes.issubset(schema_input)

    return validate_scopes


PVT_KEY_FILE = os.path.join(os.path.dirname(__file__), "id_rsa")
PVT_KEY = read_file(PVT_KEY_FILE)
PUB_KEY = read_file(os.path.join(os.path.dirname(__file__), "id_rsa.pub"))
OTHER_PUB_KEY = read_file(os.path.join(os.path.dirname(__file__),
                                       "other_rsa.pub"))
DUMMY_PUBLIC_KEY = os.path.join(os.path.dirname(__file__), "public.key")
