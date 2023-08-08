import random
from django.shortcuts import render
from django.core.mail import send_mail
from django.urls import reverse

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import generics, viewsets

from user_profile.serializers import ProfileSerializer, UserSerializer, PasswordResetEmailSerializer, PasswordResetSerializer, OTPSerializer
from user_profile.models import UserProfile, User
from config import settings


class ProfileAPIView(generics.RetrieveUpdateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = ProfileSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    

@api_view(['POST'])
def send_password_reset_email(request):
    
    """Функция для отправки почты с разовым кодом верификации"""
    
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


@api_view(['POST'])
def enter_otp_code(request):
    serializer = OTPSerializer(data=request.data)
    if serializer.is_valid():
        code = serializer.validated_data['code']

        # Get the code and email from the session
        code_from_session = request.session.get('password_reset_code')
        email_from_session = request.session.get('password_reset_email')

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


@api_view(['POST'])
def update_password(request):
    serializer = PasswordResetSerializer(data=request.data)
    if serializer.is_valid():
        
        new_password = serializer.validated_data['new_password']   
        confirm_password = serializer.validated_data['confim_password']     
        email_from_session = request.session.get('password_reset_email')
        user = User.objects.get(email=email_from_session)

        if user:
            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()

            # Clear the session after password update
            del request.session['password_reset_code']
            del request.session['password_reset_email']

            return Response({'message': 'Пароль успешно изменен'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Проверьте введенные данные'}, status=status.HTTP_400_BAD_REQUEST)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
 


