from django.urls import path
from . import views

urlpatterns = [
    path('api/rates/', views.rates),
    path('api/convert/', views.convert),
]
