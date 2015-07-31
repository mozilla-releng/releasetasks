rm -rf test
virtualenv test
source test/bin/activate
pip install tox
tox -e py27
