# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Esteban J. G. Gabancho.
#
# Invenio-Flow is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio-Flow permissions."""

from functools import wraps


def need_permission(action):
    """."""
    def need_permission_decorator(f):
        @wraps(f)
        def inner(self, *args, **kwargs):
            # TODO
            return f(self, *args, **kwargs)
        return inner
    return need_permission_decorator
