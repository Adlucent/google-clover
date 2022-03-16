# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import date

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from rest_framework_api_key.models import AbstractAPIKey
from rest_framework_api_key.models import BaseAPIKeyManager


class Application(models.Model):
    name = models.CharField(max_length=64, unique=True)
    active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "1. Application"
        verbose_name_plural = "1. Applications"

    def __str__(self):
        return self.name


class ApplicationAPIKeyManager(BaseAPIKeyManager):
    def get_usable_keys(self):
        return super().get_usable_keys().filter(application__active=True)


class ApplicationAPIKey(AbstractAPIKey):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="api_key")

    class Meta(AbstractAPIKey.Meta):
        verbose_name = "2. Application API key"
        verbose_name_plural = "2. Application API keys"
        ordering = ['-application', '-created']

    def __str__(self):
        return f'{self.application.name} | {self.name}'


class Account(models.Model):
    name = models.CharField(max_length=64, unique=True)
    user = models.ManyToManyField(User, related_name="user_account", blank=True)
    app = models.ManyToManyField(ApplicationAPIKey, related_name="app_account", blank=True)

    class Meta:
        verbose_name = "3. Account"
        verbose_name_plural = "3. Accounts"

    def __str__(self):
        return f'{self.name}'


class TrainingDataSet(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="account_data")
    name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=256)
    location = models.CharField(max_length=256, blank=True,
                                help_text="This field is not required but might help you keep track of your data and "
                                          "which training data set you are using.  For example, this can be a Big "
                                          "Query table")
    start_date = models.DateField(help_text="Enter the initial date contained for the data that was used to create "
                                            "the training data set")
    end_date = models.DateField(help_text="Enter the last date contained for the data that was used to create "
                                          "the training data set")
    update_date = models.DateField(default=date.today,
                                   help_text="Enter the date the training data set was created or updated.")

    data_fields = models.JSONField(help_text='Enter all of fields that are contained in your data set along with '
                                             'their data type, and whether they are Nullable or Required. Here is an '
                                             'example on how to enter one feature: '
                                             '['
                                             '  {'
                                             '    "name": "feature_1", '
                                             '    "type": "STRING", '
                                             '    "mode": "Nullable"'
                                             '  }'
                                             ']')

    class Meta:
        verbose_name = "4. Training Data Set"
        verbose_name_plural = "4. Training Data Sets"

    def __str__(self):
        return f'{self.account.name} | {self.name}'


class TypeOfModel(models.IntegerChoices):
    # TODO: Add other types of models that you might need to support
    VERTEX = 0, "VERTEX AI"
    PARETO_NBD = 1, "PARETO / NBD"
    BGNBD = 2, "BG / NBD"


class CLVModel(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="account_clvmodel")
    data_set = models.ForeignKey(TrainingDataSet, on_delete=models.CASCADE, related_name="data_clvmodel")
    name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=256, blank=True)
    type = models.IntegerField(choices=TypeOfModel.choices)
    data_fields = models.JSONField(help_text='Enter all of fields that are contained in your data set along with '
                                             'their data type, and whether they are Nullable or Required. Here is an '
                                             'example on how to enter one feature: '
                                             '['
                                             '  {'
                                             '    "name": "feature_1", '
                                             '    "type": "STRING", '
                                             '    "mode": "Nullable"'
                                             '  }'
                                             ']')
    training_date = models.DateField()
    metric = models.CharField(max_length=64, blank=True,
                              help_text="Name of Predicted Metric at the time of prediction. This will enable clover"
                                        "to predict future value of the metric")
    address = models.JSONField(verbose_name="Model API Parameters")
    api_key = models.JSONField(verbose_name="Model Service Account Credentials")
    mae = models.FloatField(verbose_name='Mean Absolute Error')
    mape = models.FloatField(verbose_name='Mean Absolute Percentage Error',
                             help_text="Percent is entered from 0 - 100 %",
                             validators=[MinValueValidator(0.0), MaxValueValidator(100.0)]
                             )
    rmse = models.FloatField(verbose_name='Root Mean Squared Error')

    class Meta:
        verbose_name = "5. CLV Model"
        verbose_name_plural = "5. CLV Models"

    def __str__(self):
        return f'{self.account.name} | {self.data_set.name} | {self.name}'


class BestModel(models.IntegerChoices):
    RMSE = 0, "Root Mean Squared Error"
    MAE = 1, "Mean Absolute Error"
    MAPE = 2, "Mean Absolute Percentage Error"


class Config(models.Model):
    account = models.ForeignKey(Account, on_delete=models.CASCADE, related_name="account_config")
    data_set = models.ForeignKey(TrainingDataSet, on_delete=models.CASCADE, related_name="data_config")
    name = models.CharField(max_length=64, unique=True)
    predicted_metric = models.CharField(max_length=64)
    best_model = models.IntegerField(choices=BestModel.choices,
                                     help_text="Choose the default method to evaluate how clover will choose "
                                               "the best possible model")
    segment = models.CharField(max_length=64, blank=True,
                               help_text="Enter value to help organize your different models if you want")
    time_period = models.CharField(max_length=64,
                                   help_text="Enter description of what the horizon of the prediction for the model "
                                             "is.  For example, 3-Month LTV, 1-Year LTV, etc...")

    class Meta:
        verbose_name = "6. Configuration"
        verbose_name_plural = "6. Configurations"

    def __str__(self):
        return f'{self.account.name} | {self.name} | {self.data_set.name}'
