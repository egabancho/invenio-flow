# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 Esteban J. G. Gabancho.
#
# Invenio-Flow is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Python 2/3 compatibility helpers."""

import sys

PY3 = sys.version_info[0] == 3

string_types = str if PY3 else basestring
