""" URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from apps.clover import views
from django.conf import settings
from django.conf.urls import include
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from rest_framework import routers
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    path('grappelli/', include('grappelli.urls')),  # grappelli URLS
    path('admin/clover/applicationapikey/add/', views.ApplicationAPIKeyView.as_view(), name='application_api_key'),
    path('admin/', admin.site.urls, name='admin'),
    path('api/token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', jwt_views.TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', jwt_views.TokenVerifyView.as_view(), name='token_verify'),
    path('api/endpoints/', views.APIEndpointsView.as_view(), name='endpoints'),
    path('api/apikey/', views.ApplicationAPIKeyView.as_view(), name='application_api_key'),
    path('api/config/', views.ConfigListView.as_view(), name='config-list'),
    path('api/config/<int:config_id>/clvmodels/', views.CLVModelListView.as_view(), name="clvmodel-list"),
    path('api/config/<int:config_id>/predict/', views.Predict.as_view(), name="predict"),
    path('api/config/<int:config_id>/predictfuture/', views.PredictFuture.as_view(), name="predict-future"),
    path('api/config/<int:config_id>/<int:model_id>/predict/', views.ModelPredict.as_view(), name="model-predict"),
    path('api/config/<int:config_id>/<int:model_id>/predictfuture/', views.ModelPredictFuture.as_view(),
         name="model-predict-future"),

]  # + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
