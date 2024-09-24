from django.shortcuts import render
from django.shortcuts import render

# Create your views here.
from . models import FailedLoginAttempt,User
from rest_framework.response import Response
from .serializers import CustomeuserregisterSerializer,LoginSerializer
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone




def get_tokens_for_user(user):
  refresh = RefreshToken.for_user(user)
  return {
      'refresh': str(refresh),
      'access': str(refresh.access_token),
  }


class UserRegistrationView(APIView):
  def post(self, request, format=None):
    serializer = CustomeuserregisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.save()
    token = get_tokens_for_user(user)
    return Response({'token':token, 'msg':'Registration Successful'}, status=status.HTTP_201_CREATED)



class UserLoginView(APIView):
    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')
        user = authenticate(email=email, password=password)

        if user is not None:
            # Check if failed attempts exist and handle password change requirement
            failed_attempts = FailedLoginAttempt.objects.filter(user=user).first()
            if failed_attempts and failed_attempts.password_change_required:
                return Response({'errors': {'non_field_errors': ['You must change your password before logging in.']}}, status=status.HTTP_400_BAD_REQUEST)

            # Reset failed login attempts on successful login
            if failed_attempts:
                failed_attempts.reset_attempts()

            token = get_tokens_for_user(user)
            return Response({'token': token, 'msg': 'Login Success'}, status=status.HTTP_200_OK)

        # Return error for invalid credentials
        return Response({'errors': {'non_field_errors': ['Invalid credentials']}}, status=status.HTTP_400_BAD_REQUEST)
