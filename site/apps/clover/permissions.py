# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework_api_key.permissions import BaseHasAPIKey

from .models import ApplicationAPIKey


class HasApplicationAPIKey(BaseHasAPIKey):
    model = ApplicationAPIKey
