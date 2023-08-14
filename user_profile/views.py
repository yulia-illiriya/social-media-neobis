import random
from datetime import timedelta, timezone
from django.shortcuts import render
from django.core.mail import send_mail
from django.urls import reverse

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import generics, viewsets
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.exceptions import APIException
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

from drf_yasg.utils import swagger_auto_schema

from user_profile.serializers import (
                                    ProfileSerializer, 
                                    UserSerializer,
                                    PasswordResetEmailSerializer,
                                    PasswordResetSerializer,
                                    OTPSerializer,
                                    RememberMeTokenObtainPairSerializer
                                    )
from user_profile.models import UserProfile, User
from config import settings

from django.core.cache import cache


class ProfileAPIView(generics.RetrieveUpdateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = ProfileSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    
class LogoutView(APIView):    
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)
    

class SendPasswordResetEmailView(APIView):
    @swagger_auto_schema(
        request_body=PasswordResetEmailSerializer,
        responses={
            status.HTTP_200_OK: 'Password reset code sent successfully.',
            status.HTTP_400_BAD_REQUEST: 'Invalid input data or error response.'
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = PasswordResetEmailSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)

            if user:
                code = random.randint(1000, 9999)

                # Save the code and email in the session
                request.session['password_reset_code'] = code
                request.session['password_reset_email'] = email

                # Send the code to the user's email
                subject = 'Password Reset Code'
                message = f'Ваш код сброса пароля - {code}'
                from_email = settings.EMAIL_HOST_USER
                recipient_list = [email]
                send_mail(subject, message, from_email, recipient_list, fail_silently=False)

                next_page = reverse('verify')

                response_data = {
                    'message': 'Password reset code sent successfully.',
                    'next_page': next_page
                }

                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Такой пользователь не найден. Пожалуйста, проверьте введенные данные'}, status=status.HTTP_404_NOT_FOUND)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EnterOTPCodeView(APIView):
    @swagger_auto_schema(
        request_body=OTPSerializer,
        responses={
            status.HTTP_200_OK: 'Request confirmed.',
            status.HTTP_400_BAD_REQUEST: 'Invalid input data or error response.'
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = OTPSerializer(data=request.data)
        if serializer.is_valid():
            code = serializer.validated_data['code']

            # Get the code and email from the session
            code_from_session = self.request.session.get('password_reset_code')
            email_from_session = self.request.session.get('password_reset_email')

            if code_from_session == code and email_from_session:
                next_page = reverse('reset-password')
                response_data = {
                    'message': 'Запрос подтвержден',
                    'next_page': next_page
                }

                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Неправильный код сброса'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UpdatePasswordView(APIView):
    @swagger_auto_schema(
        request_body=PasswordResetSerializer,
        responses={
            status.HTTP_200_OK: 'Password updated successfully.',
            status.HTTP_400_BAD_REQUEST: 'Invalid input data or error response.'
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            new_password = serializer.validated_data['new_password']
            confirm_password = serializer.validated_data['confim_password']
            email_from_session = self.request.session.get('password_reset_email')
            user = User.objects.get(email=email_from_session)

            if user:
                if new_password == confirm_password:
                    user.set_password(new_password)
                    user.save()

                    # Clear the session after password update
                    del self.request.session['password_reset_code']
                    del self.request.session['password_reset_email']

                    return Response({'message': 'Пароль успешно изменен'}, status=status.HTTP_200_OK)
                else:
                    return Response({'error': 'Пароли не совпадают'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'error': 'Пользователь не найден'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RememberMeTokenRefreshView(TokenRefreshView):
    
    """Передается дополнительный параметр 'запомни меня' """
    
    serializer_class = RememberMeTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        try:
            remember = request.data['remember_me']
            if remember:
                settings.SESSION_EXPIRE_AT_BROWSER_CLOSE = False
        except KeyError:
                settings.SESSION_EXPIRE_AT_BROWSER_CLOSE = True
 
        return super().post(request, *args, **kwargs)

