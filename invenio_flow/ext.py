# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Esteban J. G. Gabancho.
#
# Invenio-Flow is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio-Flow is a module for managing sinple backend workflows."""

from __future__ import absolute_import, print_function

from werkzeug.utils import import_string

from . import config
from ._compat import string_types
from .api import Flow, Task


def obj_or_import_string(value, default=None):
    """Import string or return object.

    :params value: Import path or class object to instantiate.
    :params default: Default object to return if the import fails.
    :returns: The imported object.
    """
    if isinstance(value, string_types):
        return import_string(value)
    elif value:
        return value
    return default


class InvenioFlow(object):
    """Invenio-Flow extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.app = app
            self.init_app(app)

    @property
    def flows(self):
        """Get the flow configuration key from config."""
        return self.app.config['FLOW_FACTORIES']

    def get_flow_class(self, flow_name):
        """Get flow class from configuration or default."""
        flow_cfg = self.flows[flow_name]
        return obj_or_import_string(flow_cfg.get('flow_class', None), Flow)

    def get_flow_build_func(self, flow_name):
        """Get the flow build function from configuration."""
        flow_cfg = self.flows[flow_name]
        return obj_or_import_string(flow_cfg['build_func'])

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions['invenio-flow'] = self

    def init_config(self, app):
        """Initialize configuration."""
        for k in dir(config):
            if k.startswith('FLOW_'):
                app.config.setdefault(k, getattr(config, k))
