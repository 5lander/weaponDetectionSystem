from django.shortcuts import render, redirect

def loginPage(request):
    return render(request, 'detection/login.html',{})

def registerPage(request):
    return render(request, 'detection/register.html',{})

def home(request):
    return render(request, 'detection/dashboard.html',{})