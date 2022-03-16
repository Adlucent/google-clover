# -*- coding: utf-8 -*-
from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Application
from .models import ApplicationAPIKey
from .models import Config
from .models import CLVModel


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'username', 'email', 'groups']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']


class ApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Application
        fields = ["name"]


class ApplicationAPIKeySerializer(serializers.ModelSerializer):
    application = serializers.CharField(source="application.name", max_length=64)

    class Meta:
        model = ApplicationAPIKey
        fields = ["name", "application", "expiry_date"]

    def save(self):
        name = self.validated_data['name']
        app_name = self.validated_data['application']['name']
        expiry_date = self.validated_data.get("expiry_date", None)

        if Application.objects.filter(name=app_name).exists():
            application = Application.objects.get(name=app_name)
        else:
            application = Application(name=app_name)
            application.save()

        if ApplicationAPIKey.objects.filter(name=name, application=application).exists():
            api_key = ApplicationAPIKey.objects.get(name=name, application=application)
            key = "Key has already been produced"
        else:
            api_key, key = ApplicationAPIKey.objects.create_key(
                name=name, application=application, expiry_date=expiry_date
            )

        return api_key, key


class ConfigSerializer(serializers.ModelSerializer):
    account = serializers.CharField(source='account.name')
    data_set = serializers.CharField(source='data_set.name')

    class Meta:
        model = Config
        fields = ["id", "account", "name", "predicted_metric", "best_model", "segment", "time_period", "data_set"]


class CLVModelSerializer(serializers.ModelSerializer):
    account = serializers.CharField(source='account.name')

    class Meta:
        model = CLVModel
        fields = ["id", "account", "name", "description", "type", "data_fields", "training_date",  # "address",
                  "mae", "mape", "rmse"]
