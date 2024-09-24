from rest_framework import serializers
from .models import User,FailedLoginAttempt
from django.contrib.auth.hashers import make_password
from django.utils.encoding import smart_str, force_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth import authenticate
from django.utils import timezone
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings

class CustomeuserregisterSerializer(serializers.ModelSerializer):
        # password= serializers.CharField(
        # write_only=True,
        # required=True,
        # help_text='Leave empty if no change needed',
        # style={'input_type': 'password', 'placeholder': 'Password'})
        # password2= serializers.CharField(
        # write_only=True,
        # required=True,
        # help_text='Leave empty if no change needed',
        # style={'input_type': 'password', 'placeholder': 'Password'})
        password2 = serializers.CharField(style={'input_type':'password'}, write_only=True)
        
        class Meta:
            model = User
            fields = '__all__'
        
        def validate(self, attrs):
            password = attrs.get('password')
            password2 = attrs.get('password2')
            if password != password2:
                raise serializers.ValidationError("Password and Confirm Password doesn't match")
            return attrs

        def create(self, validate_data):
            return User.objects.create_user(**validate_data)
        
        
# class LoginSerializer(serializers.Serializer):
#     name = serializers.CharField(required=True)
#     password = serializers.CharField(required=True, write_only=True)
    
#     def validate(self, data):
#         name = data.get('name')
#         password = data.get('password')

#         # Get the user object
#         user = User.objects.filter(name=name).first()

#         if not user:
#             raise serializers.ValidationError("Invalid name or password.")

#         # Check if the user is locked
#         failed_attempt = FailedLoginAttempt.objects.filter(user=user).first()
#         if failed_attempt and failed_attempt.locked:
#             raise serializers.ValidationError("Your account is locked due to too many failed attempts. Please contact support.")

#         # Authenticate the user
#         user = authenticate(name=name, password=password)  # Ensure the correct field is used for authentication

#         if user is not None:
#             # Reset failed attempts on successful login
#             if failed_attempt:
#                 failed_attempt.reset_attempts()
#         else:
#             # Update or create failed attempt record
#             if failed_attempt:
#                 failed_attempt.attempts += 1
#                 failed_attempt.last_attempt = timezone.now()

#                 if failed_attempt.attempts > 4:
#                     failed_attempt.locked = True
#             else:
#                 # Create FailedLoginAttempt with user instance
#                 failed_attempt = FailedLoginAttempt.objects.create(
#                     user=user,  # Ensure the user is set here
#                     attempts=1,
#                     last_attempt=timezone.now()
#                 )

#             failed_attempt.save()
#             self.initiate_password_reset(user)
#             raise serializers.ValidationError("Too many failed attempts. Please reset your password.")

#         return data
    
#     def initiate_password_reset(self, user):
#         # Generate a token and uid for the user
#         token = PasswordResetTokenGenerator().make_token(user)
#         uid = urlsafe_base64_encode(force_bytes(user.pk))

#         # Build the password reset link
#         reset_link = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
#         reset_url = f"{self.context['request'].scheme}://{self.context['request'].get_host()}{reset_link}"

#         # Send password reset email
#         send_mail(
#             'Reset Your Password',
#             f'Please reset your password using the following link: {reset_url}',
#             settings.DEFAULT_FROM_EMAIL,
#             [user.email],
#             fail_silently=False,
#         )

# MAX_FAILED_ATTEMPTS = 3
# LOCKOUT_DURATION = 30  # minutes
# class LoginSerializer(serializers.ModelSerializer):
#     email = serializers.EmailField(max_length=255)
#     class Meta:
#         model = User
#         fields = ['email', 'password']
    
#     def validate(self, data):
#         email = data.get('email')
#         password = data.get('password')

#         # Attempt to authenticate the user
#         user = authenticate(email=email, password=password)
        
#         if user is None:
#             # Check if there's a user with the given email
#             if User.objects.filter(email=email).exists():
#                 # Fetch or create a FailedLoginAttempt record for a valid user
#                 failed_attempt, created = FailedLoginAttempt.objects.get_or_create(user=user)
                
#                 # Increment the failed attempts count
#                 failed_attempt.attempts += 1
#                 failed_attempt.last_attempt = timezone.now()
                
#                 if failed_attempt.attempts >= MAX_FAILED_ATTEMPTS:
#                     failed_attempt.locked = True

#                 failed_attempt.save()

#                 if failed_attempt.locked:
#                     raise serializers.ValidationError('Account is blocked. Please reset your password.')

#             raise serializers.ValidationError('Invalid login credentials')

#         # If user is authenticated, reset failed attempts
#         if FailedLoginAttempt.objects.filter(user=user).exists():
#             failed_attempt = FailedLoginAttempt.objects.get(user=user)
#             failed_attempt.reset_attempts()

#         return data

MAX_FAILED_ATTEMPTS = 3

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        # Authenticate user
        user = authenticate(email=email, password=password)

        if user is None:
            # Handle the failed attempt only if the user object is valid
            user_instance = User.objects.filter(email=email).first()
            if user_instance:
                failed_attempts, created = FailedLoginAttempt.objects.get_or_create(user=user_instance)

                if not created:
                    failed_attempts.attempts += 1
                    failed_attempts.last_attempt = timezone.now()
                    if failed_attempts.attempts >= MAX_FAILED_ATTEMPTS:
                        failed_attempts.locked = True
                        failed_attempts.password_change_required = True
                    failed_attempts.save()
                
                # If the user is locked, inform them accordingly
                if failed_attempts.locked:
                    raise serializers.ValidationError({"non_field_errors": ["Account locked due to too many failed login attempts."]})
                
            raise serializers.ValidationError({"non_field_errors": ["Invalid credentials"]})

        # Check if password change is required
        failed_attempts = FailedLoginAttempt.objects.filter(user=user).first()
        if failed_attempts and failed_attempts.locked:
            raise serializers.ValidationError({"non_field_errors": ["Account locked. Please contact support."]})
        elif failed_attempts and failed_attempts.attempts >= MAX_FAILED_ATTEMPTS:
            attrs['password_change_required'] = True
        else:
            attrs['password_change_required'] = False

        attrs['user'] = user
        return attrs
