# -*- coding: utf-8 -*-

from os import path
import yaml

import arrow
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .tcutils import stable_slug_id


DEFAULT_TEMPLATE_DIR = path.join(path.dirname(__file__), "templates")

def make_task_graph(root_template="release_graph.yml.tmpl", template_dir=DEFAULT_TEMPLATE_DIR, **template_kwargs):
    env = Environment(loader=FileSystemLoader(template_dir), undefined=StrictUndefined)

    template = env.get_template(root_template)
    template_vars = {
        "stable_slug_id": stable_slug_id(),
        "now": arrow.now(),
        # This is used in defining expirations in tasks. There's no way to
        # actually tell Taskcluster never to expire them, but 1,000 years
        # is as good as never....
        "never": arrow.now().replace(years=1000),
    }
    template_vars.update(template_kwargs)

    return yaml.safe_load(template.render(**template_vars))
