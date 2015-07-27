# -*- coding: utf-8 -*-

from os import path
import yaml

from arrow import Arrow
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .tcutils import stable_slug_id


DEFAULT_TEMPLATE_DIR = path.join(path.dirname(__file__), "templates")

def make_task_graph(root_template="release_graph.yml.tmpl", template_dir=DEFAULT_TEMPLATE_DIR, **template_kwargs):
    env = Environment(loader=FileSystemLoader(template_location), undefined=StrictUndefined)

    template = env.get_template(root_template)
    template_vars = {
        "stable_slug_id": stable_slug_id,
        "now": Arrow.now(),
    }
    template_vars.update(template_kwargs)

    return yaml.safe_load(template.render(**template_vars))
