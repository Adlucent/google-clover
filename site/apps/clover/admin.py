# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from rest_framework_api_key.admin import APIKeyModelAdmin

from .models import Account
from .models import Application
from .models import ApplicationAPIKey
from .models import CLVModel
from .models import Config
from .models import TrainingDataSet


class MyAdminSite(AdminSite):
    # Text to put at the end of each page's <title>.
    site_title = _('Default Admin')

    # Text to put in each page's <h1> (and above login form).
    site_header = _('Default administration')

    # Text to put at the top of the admin index page.
    index_title = _('Default administration')


admin.site = MyAdminSite()

admin.site.site_header = mark_safe(
    '<img '
    'src = "https://3dbo2q210xna3qs2hvkeqtr1-wpengine.netdna-ssl.com/wp-content/themes/_ws/logo_light.svg" '
    'height = "40" '
    '/>'
)


class UserAdmin(admin.ModelAdmin):
    def get_queryset(self, request):
        qs = super(UserAdmin, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(id=request.user.id)


@admin.register(ApplicationAPIKey)
class ApplicationAPIKeyModelAdmin(APIKeyModelAdmin):
    pass


@admin.register(Application)
class ApplicationModelAdmin(admin.ModelAdmin):
    pass


admin.site.register(User, UserAdmin)
admin.site.register(Group)
admin.site.register(Application)
admin.site.register(ApplicationAPIKey)
admin.site.register(Account)
admin.site.register(TrainingDataSet)
admin.site.register(CLVModel)
admin.site.register(Config)
