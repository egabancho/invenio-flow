# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Esteban J. G. Gabancho.
#
# Invenio-Flow is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio-FLow proxy to the extension object"""

from flask import current_app
from werkzeug.local import LocalProxy


current_flow = LocalProxy(
    lambda: current_app.extensions['invenio-flow'])
"""Proxy to an instance of ``_InvenioFlow`` extensions."""
