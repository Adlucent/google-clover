# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import status
# from django.contrib.auth import get_user_model
# from django.contrib.auth.models import Group
from django.contrib.auth.models import User
from django.http import Http404
# from django.db.models.query_utils import DeferredAttribute
# from django.shortcuts import render
# from rest_framework import permissions
# from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ApplicationAPIKey
from .models import BestModel
from .models import CLVModel
from .models import Config
from .predict import predict
from .permissions import HasApplicationAPIKey
from .serializers import ApplicationAPIKeySerializer
from .serializers import CLVModelSerializer
from .serializers import ConfigSerializer


def get_model_or_404(request, model_class, pk):
    if request.user.is_staff:
        try:
            model = model_class.objects.get(pk=pk)
        except model_class.DoesNotExist:
            raise Http404(f"{model_class.__name__} does not exists with the passed ID: {pk}")
    elif request.user.is_anonymous:
        try:
            key = request.META["HTTP_AUTHORIZATION"].split()[1]
            api_key = ApplicationAPIKey.objects.get_from_key(key)
            model = model_class.objects.get(pk=pk, account__app=api_key.id)
        except model_class.DoesNotExist:
            raise Http404(f"API Key does not have access or {model_class.__name__} does not exists with the "
                          f"passed ID: {pk}")
    else:
        try:
            user = User.objects.get(username=request.user)
            model = model_class.objects.get(pk=pk, account__user=user.id)
        except model_class.DoesNotExist:
            raise Http404(f"User does not have access or {model_class.__name__} does not exists with the "
                          f"passed ID: {pk}\n")

    return model


def get_config_queryset_or_404(request):
    if request.user.is_staff:
        queryset = Config.objects.all()
    elif request.user.is_anonymous:
        key = request.META["HTTP_AUTHORIZATION"].split()[1]
        api_key = ApplicationAPIKey.objects.get_from_key(key)
        queryset = Config.objects.filter(account__app=api_key.id)
        if not queryset:
            raise Http404("Api Key has no access to any configurations")
    else:
        user = User.objects.get(username=request.user)
        queryset = Config.objects.filter(account__user=user.id)
        if not queryset:
            raise Http404("User has no access to any configurations")

    return queryset


class APIEndpointsView(APIView):
    permissions = [IsAuthenticated]

    def get(self, request):
        if request.user.is_authenticated:
            content = {
                "data": {
                    "version"  : "0.1",
                    "baseURL"  : "https://clover-gcp.uc.r.appspot.com",
                    "endpoints": {
                        "token"             : "/api/token/",
                        "token_refresh"     : "/api/token/refresh/",
                        "token_verify"      : "/api/token/verify/",
                        "endpoints"         : "/api/endpoints/",
                        "apikey"            : "/api/apikey/",
                        "config"            : "/api/config/",
                        "clvmodels"         : "/api/config/<int:config_id>/clvmodels/",
                        "predict"           : "/api/config/<int:config_id>/predict/",
                        "predictfuture"     : "/api/config/<int:config_id>/predictfuture/",
                        "modelpredict"      : "/api/config/<int:config_id>/<int:model_id>/predict/",
                        "modelpredictfuture": "/api/config/<int:config_id>/<int:model_id>/predictfuture/",

                    }
                }
            }
            return Response(content, status=status.HTTP_200_OK)
        else:
            return Response({"message": "User is not authenticated"}, status=status.HTTP_400_BAD_REQUEST)


class ApplicationAPIKeyView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = ApplicationAPIKeySerializer(data=request.data)

        if serializer.is_valid():
            api_key, key = serializer.save()

            if key == 'Key has already been produced':
                request.data["message"] = key
                return Response(request.data, status=status.HTTP_302_FOUND)

            request.data['api_key'] = key
            return Response(request.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ConfigListView(APIView):
    permission_classes = [HasApplicationAPIKey | IsAuthenticated]

    def get(self, request):
        try:
            queryset = get_config_queryset_or_404(request)
        except Http404 as e:
            return Response({"message": str(e)}, status=status.HTTP_404_NOT_FOUND)

        serializer = ConfigSerializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class CLVModelListView(APIView):
    permission_classes = [HasApplicationAPIKey | IsAuthenticated]

    def get(self, request, config_id):
        try:
            config = get_model_or_404(request, Config, config_id)
        except Http404 as e:
            return Response({"message": str(e)}, status=status.HTTP_404_NOT_FOUND)

        best_model = BestModel(config.best_model).name
        queryset = CLVModel.objects.filter(data_set_id=config.data_set.id).order_by(f"{best_model.lower()}")
        serializer = CLVModelSerializer(queryset, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class Predict(APIView):
    permission_classes = [HasApplicationAPIKey | IsAuthenticated]

    def post(self, request, config_id, future=False):
        response = {"message": ""}
        try:
            config = get_model_or_404(request, Config, config_id)
        except Http404 as e:
            return Response({"message": str(e)}, status=status.HTTP_404_NOT_FOUND)

        best_model = BestModel(config.best_model).name

        clvmodel = CLVModel.objects.filter(data_set_id=config.data_set.id).order_by(f"{best_model.lower()}")[:1]

        if clvmodel:
            clvmodel = clvmodel[0]
            response = predict(request, config, clvmodel, future)
            response["metric"] = config.predicted_metric

            if response["message"] == "":
                response_status = status.HTTP_200_OK
            else:
                response_status = status.HTTP_400_BAD_REQUEST
        else:
            response["message"] += f'Could not call generate predictions as there were no valid models\n'
            response_status = status.HTTP_404_NOT_FOUND

        return Response(response, status=response_status)


class PredictFuture(Predict):
    permission_classes = [HasApplicationAPIKey | IsAuthenticated]

    def post(self, request, config_id, future=True):
        return super(PredictFuture, self).post(request, config_id, future=True)


class ModelPredict(APIView):
    permission_classes = [HasApplicationAPIKey | IsAuthenticated]

    def post(self, request, config_id, model_id, future=False):
        try:
            config = get_model_or_404(request, Config, config_id)
        except Http404 as e:
            return Response({"message": str(e)}, status=status.HTTP_404_NOT_FOUND)

        try:
            clvmodel = get_model_or_404(request, CLVModel, model_id)
        except Http404 as e:
            return Response({"message": str(e)}, status=status.HTTP_404_NOT_FOUND)

        response = predict(request, config, clvmodel, future)
        response["metric"] = config.predicted_metric

        if response["message"] == "":
            response_status = status.HTTP_200_OK
        else:
            response_status = status.HTTP_400_BAD_REQUEST

        return Response(response, response_status)


class ModelPredictFuture(ModelPredict):
    permission_classes = [HasApplicationAPIKey | IsAuthenticated]

    def post(self, request, config_id, model_id, future=True):
        return super(ModelPredictFuture, self).post(request, config_id, model_id, future=True)
