from django.urls import path

from .views import UserRegistrationView,UserLoginView

urlpatterns = [
    path('userregister/',UserRegistrationView.as_view(),name='userregister'),
    path('login/', UserLoginView.as_view(), name='login')
]