# -*- coding: utf-8 -*-
import arrow
import yaml

from functools import partial
from os import path
from chunkify import chunkify
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from taskcluster.utils import stableSlugId, encryptEnvVar

from releasetasks.util import (
    treeherder_platform, sign_task, buildbot2ftp, buildbot2bouncer,
    get_json_rev)

DEFAULT_TEMPLATE_DIR = path.join(path.dirname(__file__), "templates")


def make_task_graph(public_key, signing_pvt_key, product, root_home_dir,
                    root_template="release_graph.yml.tmpl",
                    template_dir=DEFAULT_TEMPLATE_DIR,
                    **template_kwargs):
    # TODO: some validation of template_kwargs + defaults
    env = Environment(
        loader=FileSystemLoader([path.join(template_dir, root_home_dir), path.join(template_dir, 'notification')]),
        undefined=StrictUndefined,
        extensions=['jinja2.ext.do'])

    now = arrow.now()
    now_ms = now.timestamp * 1000

    # Don't let the signing pvt key leak into the task graph.
    with open(signing_pvt_key) as f:
        pvt_key = f.read()

    template = env.get_template(root_template)
    template_vars = {
        "product": product,
        "stableSlugId": stableSlugId(),
        "chunkify": chunkify,
        "sorted": sorted,
        "now": now,
        "now_ms": now_ms,
        # This is used in defining expirations in tasks. There's no way to
        # actually tell Taskcluster never to expire them, but 1,000 years
        # is as good as never....
        "never": arrow.now().replace(years=1000),
        "pushlog_id": get_json_rev(template_kwargs["repo_path"],
                                   template_kwargs["revision"])["pushid"],
        "get_treeherder_platform": treeherder_platform,
        "encrypt_env_var": lambda *args: encryptEnvVar(*args,
                                                       keyFile=public_key),
        "buildbot2ftp": buildbot2ftp,
        "buildbot2bouncer": buildbot2bouncer,
        "sign_task": partial(sign_task, pvt_key=pvt_key),
    }
    template_vars.update(template_kwargs)

    return yaml.safe_load(template.render(**template_vars))
