# -*- coding: utf-8 -*-
#
# Copyright (C) 2019, 2020 Esteban J. G. Gabancho.
#
# Invenio-Flow is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio-Flow is a module for managing sinple backend workflows."""

from __future__ import absolute_import, print_function

from .api import Flow
from .decorators import task
from .ext import InvenioFlow
from .version import __version__

__all__ = ('__version__', 'InvenioFlow', 'Flow', 'task')
