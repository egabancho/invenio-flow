# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Esteban J. G. Gabancho.
#
# Invenio-Flow is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from __future__ import absolute_import, print_function

from flask import Flask

from invenio_flow import InvenioFlow


def test_version():
    """Test version import."""
    from invenio_flow import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = InvenioFlow(app)
    assert 'invenio-flow' in app.extensions

    app = Flask('testapp')
    ext = InvenioFlow()
    assert 'invenio-flow' not in app.extensions
    ext.init_app(app)
    assert 'invenio-flow' in app.extensions
