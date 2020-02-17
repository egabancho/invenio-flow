# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Esteban J. G. Gabancho.
#
# Invenio-Flow is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Useful decorators."""

from celery import shared_task

from .api import Task


def task(*args, **kwargs):
    """Wrapper around shared task to set default base class."""
    kwargs.setdefault('base', Task)
    return shared_task(*args, **kwargs)
