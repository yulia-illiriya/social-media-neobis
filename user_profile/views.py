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
from rest_framework.exceptions import ValidationError, APIException

from drf_yasg.utils import swagger_auto_schema

from user_profile.serializers import (
                                    ProfileSerializer, 
                                    UserSerializer,
                                    PasswordResetEmailSerializer,
                                    PasswordResetSerializer,
                                    OTPSerializer,
                                    RememberMeTokenObtainPairSerializer,
                                    
                                    )
from user_profile.models import UserProfile, User, PasswordReset
from config import settings

from django.core.cache import cache


class ProfileAPIViewList(generics.ListAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = ProfileSerializer
    

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
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise ValidationError("User with this email wasn't found.")
            
            
            while True:
                code = random.randint(1000, 9999)

                if not PasswordReset.objects.filter(code=code).exists():
                    break 
                                            
            PasswordReset.objects.create(email=email, code=code)            

                
            subject = 'Password Reset Code'
            message = f'Ваш код сброса пароля - {code}'
            from_email = settings.EMAIL_HOST_USER
            recipient_list = [email]
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)

            next_page = reverse('verify')

            response_data = {
                    'message': 'Password reset code sent successfully. Check your email',
                    'next_page': next_page
                }

            return Response(response_data, status=status.HTTP_200_OK)

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
        data = request.data        
        
        password_reset = PasswordReset.objects.filter(code=data['code']).first()
        
        if not password_reset or data['code'] != password_reset.code:
            raise APIException('Код подтверждения неверен. Проверьте корректность данных', status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=password_reset.email)
        except User.DoesNotExist:
            raise ValidationError("User with this email wasn't found", status=status.HTTP_400_BAD_REQUEST)
        
        next_page = reverse('reset-password')
        user_id = user.pk
        
        response_data = {
                    'message': 'Запрос подтвержден',
                    'next_page': next_page,
                    "user_id": user_id
                }

        return Response(response_data, status=status.HTTP_200_OK)


class UpdatePasswordView(APIView):
    @swagger_auto_schema(
        request_body=PasswordResetSerializer,
        responses={
            status.HTTP_200_OK: 'Password updated successfully.',
            status.HTTP_400_BAD_REQUEST: 'Invalid input data or error response.'
        }
    )
    def post(self, request, *args, **kwargs):
        data = request.data
        user_id = data.get('user_id')
        user = User.objects.get(user_id)   
        
        serializer = PasswordResetSerializer(data=request.data)

        if serializer.is_valid():
            if data['new_password'] != data['confirm_password']:
                return Response({"password": "Password fields didn't match."}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(data['new_password'])
            user.save()

            return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)

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

