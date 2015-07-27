# -*- coding: utf-8 -*-


from jinja2 import Template, StrictUndefined

from .tcutils import stable_slug_id

def make_task_graph(template_stream, **template_kwargs):
    #env = Environment(loader=FileSystemLoader(template_location), undefined=StrictUndefined)
    template = Template(template_stream.read())
    template_vars = {
        "stable_slug_id": stable_slug_id,
        "now": something,
    }
    template_vars.update(template_kwargs)

    return yaml.safe_load(template.render(**template_vars))
