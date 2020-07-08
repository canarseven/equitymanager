from django.http import HttpResponse
from django.shortcuts import render


# Create your views here.


def index(request):
    return render(request, "analyst/index.html")


def dcf(request):
    return render(request, "analyst/dcf-calculator.html")
