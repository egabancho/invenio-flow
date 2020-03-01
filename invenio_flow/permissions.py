# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Esteban J. G. Gabancho.
#
# Invenio-Flow is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio-Flow permissions."""

from functools import wraps

from flask import abort

from .proxies import current_flow


def need_permission(args_getter, action):
    """Get permission for flows or abort."""
    def need_permission_decorator(f):
        @wraps(f)
        def inner(self, flow_name, *args, **kwargs):
            permission_factory = current_flow.get_permission_factory(
                flow_name
            )(action)

            permission = permission_factory(
                args_getter(self, flow_name=flow_name, *args, **kwargs)
            )

            if permission is not None and not permission.can():
                abort(404)  # Hide existing URLs for more security

            return f(self, flow_name, *args, **kwargs)
        return inner
    return need_permission_decorator


def default_permission_factory(action):
    """Default permission factory, allow all."""
    def allow(*args, **kwargs):
        def can(self):
            return True
        return type('MyPermissionChecker', (), {'can': can})()

    def deny(*args, **kwargs):
        def can(self):
            return False
        return type('MyPermissionChecker', (), {'can': can})()

    def task_actions(flow, task_id):
        return allow()

    def flow_create(flow_name, payload):
        return allow()

    def flow_actions(flow, payload=None):
        return allow()

    _actions = {
        'flow-create': flow_create,
        'flow-status': flow_actions,
        'flow-start': flow_actions,
        'flow-restart': flow_actions,
        'flow-stop': flow_actions,
        'flow-task-start': task_actions,
        'flow-task-restart': task_actions,
        'flow-task-stop': task_actions,
    }

    return _actions.get(action, deny)
