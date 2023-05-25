from django.urls import path, include

from . import views

urlpatterns = [
    path('', views.index),
    path('app/', views.app),
    path('accounts/login/', views.CustomLoginView.as_view()),
    path('accounts/register/', views.register),
    path('accounts/', include('django.contrib.auth.urls')),
]
