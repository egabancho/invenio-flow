# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Esteban J. G. Gabancho.
#
# Invenio-Flow is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio-Flow is a module for managing simple backend workflows."""

FLOW_FACTORIES = {}
"""Define your application flows and options for them.

The structure of the dictionary is as follows:

.. code-block:: python

    def build_flow(flow):
        flow.chain(t1)
        flow.group(t2, [{'param': 'value}, {'param': 'value}])
        flow.chain([t3, t4])
        return flow


    def flow_permission_factory(action):
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


    FLOW_FACTORIES = {
        'my-flow-name': {
            'flow_imp': build_flow,
            'permission_factory_imp': flow_permission_factory
        },
        ...
    }
"""
