# -*- coding: utf-8 -*-
import arrow
import yaml

from functools import partial
from os import path
from chunkify import chunkify
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from taskcluster.utils import encryptEnvVar

from releasetasks.util import (
    treeherder_platform, sign_task, buildbot2ftp, buildbot2bouncer,
    get_json_rev, sort_tasks, graph_to_tasks, add_atomic_task,
    inject_dummy_tasks, inject_taskGroupId, slug_id, stable_slug_id
)

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
        "stableSlugId": stable_slug_id(),
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


def make_tasks(public_key, signing_pvt_key, product, root_home_dir,
               root_template="release_graph.yml.tmpl",
               template_dir=DEFAULT_TEMPLATE_DIR,
               **template_kwargs):
    graph = make_task_graph(
        public_key, signing_pvt_key, product, root_home_dir,
        root_template, template_dir, **template_kwargs)
    tasks = graph_to_tasks(graph)
    with open(signing_pvt_key) as f:
        pvt_key = f.read()
    toplevel_task_id = slug_id()
    env = Environment(
        loader=FileSystemLoader([
            path.join(template_dir, root_home_dir),
            path.join(template_dir, 'notification'),
            path.join(template_dir, 'shared'),
        ]),
        undefined=StrictUndefined,
        extensions=['jinja2.ext.do'])
    template = env.get_template("atomic_task.yml.tmpl")
    template_vars = {
        "product": product,
        "now": arrow.now(),
        "never": arrow.now().replace(years=1000),
        "sorted": sorted,
        "stableSlugId": stable_slug_id(),
        "sign_task": partial(sign_task, pvt_key=pvt_key),
    }
    template_vars.update(template_kwargs)
    toplevel_task = yaml.safe_load(template.render(**template_vars))

    dummy_task_template = env.get_template("dummy_task.yml.tmpl")
    dummy_task = yaml.safe_load(dummy_task_template.render(**template_vars))
    tasks = inject_dummy_tasks(tasks, dummy_task)
    tasks = add_atomic_task(tasks, (toplevel_task_id, toplevel_task))
    taskGroupId = slug_id()
    tasks = inject_taskGroupId(tasks, taskGroupId)
    return taskGroupId, toplevel_task_id, sort_tasks(tasks)
