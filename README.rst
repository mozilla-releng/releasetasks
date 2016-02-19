===============================
Release Graphs
===============================

Mozilla Release Promotion Tasks contains code to generate release-related Taskcluster graphs.

* Free software: MPL license

Features
--------

* TODO

Testing
-------

Example test invocation using docker:
  docker run --rm -v `pwd`:/src -ti rail/python-test-runner /bin/sh -c "cd /src && tox"

Or to run a single test:
  docker run --rm -v `pwd`:/src -ti rail/python-test-runner /bin/sh -c "cd /src && .tox/py27/bin/py.test --verbose --cov=releasetasks --cov-report term-missing --doctest-modules releasetasks/test/test_updates.py::TestUpdates::test_requires"
