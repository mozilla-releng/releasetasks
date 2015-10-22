# -*- coding: utf-8 -*-

from os import path
import yaml
import arrow
from chunkify import chunkify
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from thclient import TreeherderClient
from taskcluster.utils import stableSlugId, encryptEnvVar

from releasetasks.util import treeherder_platform
from release.platforms import buildbot2ftp, buildbot2bouncer

DEFAULT_TEMPLATE_DIR = path.join(path.dirname(__file__), "templates")


def make_task_graph(public_key, root_template="release_graph.yml.tmpl",
                    template_dir=DEFAULT_TEMPLATE_DIR, **template_kwargs):
    # TODO: some validation of template_kwargs + defaults
    env = Environment(loader=FileSystemLoader(template_dir),
                      undefined=StrictUndefined)
    th = TreeherderClient()

    now = arrow.now()
    now_ms = now.timestamp * 1000

    template = env.get_template(root_template)
    template_vars = {
        "stableSlugId": stableSlugId(),
        "chunkify": chunkify,
        "sorted": sorted,
        "now": now,
        "now_ms": now_ms,
        # This is used in defining expirations in tasks. There's no way to
        # actually tell Taskcluster never to expire them, but 1,000 years
        # is as good as never....
        "never": arrow.now().replace(years=1000),
        # Treeherder expects 12 symbols in revision
        "revision_hash": th.get_resultsets(
            template_kwargs["branch"],
            revision=template_kwargs["revision"][:12])[0]["revision_hash"],
        "get_treeherder_platform": treeherder_platform,
        "encrypt_env_var": lambda *args: encryptEnvVar(*args,
                                                       keyFile=public_key),
        "buildbot2ftp": buildbot2ftp,
        "buildbot2bouncer": buildbot2bouncer,
    }
    template_vars.update(template_kwargs)

    return yaml.safe_load(template.render(**template_vars))
