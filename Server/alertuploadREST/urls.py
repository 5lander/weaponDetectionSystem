from . import views
from django.urls import path, include

urlpatterns = [
    # Alert POST
    path('images/', views.postAlert, name='postalert'),

]