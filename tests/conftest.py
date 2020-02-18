# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Esteban J. G. Gabancho.
#
# Invenio-Flow is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

from __future__ import absolute_import, print_function

import pytest
from flask import Flask
from flask_babelex import Babel
from invenio_celery import InvenioCelery
from invenio_db import InvenioDB

from invenio_flow import InvenioFlow


@pytest.fixture(scope='module')
def celery_config_ext(celery_config_ext):
    """Celery configuration."""
    celery_config_ext['CELERY_TASK_EAGER_PROPAGATES_EXCEPTIONS'] = False
    return celery_config_ext


@pytest.fixture(scope='module')
def create_app(instance_path):
    """Application factory fixture."""
    def factory(**config):
        app = Flask('testapp', instance_path=instance_path)
        app.config.update(**config)
        Babel(app)
        InvenioDB(app)
        InvenioCelery(app)
        InvenioFlow(app)
        return app

    return factory
