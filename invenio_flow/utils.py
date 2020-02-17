# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Esteban J. G. Gabancho.
#
# Invenio-Flow is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio-Flow utils."""

from uuid import uuid4


def uuid(_uuid=uuid4):
    """Generate unique id in UUID4 format.

    See Also:
        For now this is provided by :func:`uuid.uuid4`.
    """
    return str(_uuid())
