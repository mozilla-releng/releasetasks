# -*- coding: utf-8 -*-

from os import path
import yaml

import arrow
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .tcutils import stable_slug_id


DEFAULT_TEMPLATE_DIR = path.join(path.dirname(__file__), "templates")



def make_task_graph(root_template="release_graph.yml.tmpl", template_dir=DEFAULT_TEMPLATE_DIR, **template_kwargs):
    # TODO: some validation of template_kwargs + defaults
    env = Environment(loader=FileSystemLoader(template_dir), undefined=StrictUndefined)

    now = arrow.now()
    now_ms = now.timestamp * 1000

    template = env.get_template(root_template)
    template_vars = {
        "stable_slug_id": stable_slug_id(),
        "now": now,
        "now_ms": now_ms,
        # This is used in defining expirations in tasks. There's no way to
        # actually tell Taskcluster never to expire them, but 1,000 years
        # is as good as never....
        "never": arrow.now().replace(years=1000),
        "get_complete_mar_url": lambda a, b, c, d: "COMPLETE MAR URL",
        "get_complete_mar_artifact": lambda a, b, c: "COMPLETE MAR ARTIFACT",
        # TODO: this should be a hash of the revisions in the push
        "revision_hash": "abcdef",
        "get_treeherder_platform": lambda p: p,
        # TODO: unstub this
        "encrypt_env_var": lambda a, b, c, d, e: "ENCRYPTED",
    }
    template_vars.update(template_kwargs)

    return yaml.safe_load(template.render(**template_vars))
