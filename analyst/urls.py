from django.urls import path, re_path
from django.views.generic import TemplateView

from . import views

urlpatterns = [
    re_path(r'^$', TemplateView.as_view(template_name='index.html'), name='home'),
    re_path(r'^index.html', TemplateView.as_view(template_name='index.html'), name='home'),
    path('dcf-calculator.html', views.get_dcf, name='dcf-calculator')
]
