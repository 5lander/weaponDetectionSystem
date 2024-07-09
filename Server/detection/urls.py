
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

#app_name = AppName

urlpatterns = [
    path('login/', views.loginPage, name='login'),
    path('register/', views.registerPage, name='register'),
    path('', views.home, name='home'),
    path('logout/', views.logoutUser, name='logout'),

    path('resetpassword/',
         auth_views.PasswordResetView.as_view(template_name = "detection/password_reset.html"),
         name ='resetpassword'),
    path('resetpasswordsent/',
         auth_views.PasswordResetDoneView.as_view(template_name = "detection/password_reset_sent.html"),
         name ='resetpasswordsent'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name = "detection/password_reset_form.html"),
         name ='resetpasswordsent'),
    path('resetpasswordcomplete/',
         auth_views.PasswordResetCompleteView.as_view(template_name = "detection/password_reset_done.html"),
         name ='resetpasswordcomplete'),
    path('alert/<uuid:pk>/',views.alert, name='alert'),         

]