from django.urls import path
from . import views

urlpatterns = [
    path('', views.search, name="analysis-search"),
    path('analysis/', views.home, name="analysis-home"),
    path('about/', views.about, name="analysis-about")
]
