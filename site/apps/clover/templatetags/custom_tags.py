# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import template
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe


register = template.Library()

# @register.simple_tag(takes_context = True)
# def is_superuser(format_string):
#     return datetime.datetime.now().strftime(format_string)


# {% load user.is_superuser super_user %}
# <ul class="grp-horizontal-list">
#     <li><a href="{% if super_user %}/dashboard{% else %}{% url 'admin:index' %}{% endif %}">{% trans "Home" %}</a>
#     </li>
# </ul>
