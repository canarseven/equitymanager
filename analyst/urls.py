from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('index.html', views.index, name='index'),
    path('dcf-calculator.html', views.get_dcf, name='dcf-calculator')
]