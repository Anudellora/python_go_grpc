from django.urls import path
from . import views
urlpatterns = [path("checks", views.checks, name="checks"), path("", views.index, name="index"), path("grpc", views.direct, name="grpc"), path("nginx", views.proxy, name="nginx"), path("health", views.health, name="health")]
