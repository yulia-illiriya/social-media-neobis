import random
from datetime import timedelta, timezone
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

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
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework import filters
from rest_framework_simplejwt.authentication import JWTAuthentication

from dj_rest_auth.registration.serializers import SocialLoginSerializer
from dj_rest_auth.registration.views import SocialLoginView

from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client

from drf_yasg.utils import swagger_auto_schema

from user_profile.serializers import (
                                    ProfileSerializer, 
                                    UserSerializer,
                                    PasswordResetEmailSerializer,
                                    PasswordResetSerializer,
                                    OTPSerializer,
                                    RememberMeTokenObtainPairSerializer,
                                    UserFollowSerializer,
                                    SimpleProfileSerializer,
                                    FollowerSerializer,
                                    FollowSerializer,
                                    PhotoProfileSerializer
                                    )
from user_profile.models import UserProfile, User, PasswordReset, Follower
from user_profile.paginations import CustomLimitOffsetPagination
from config import settings
from rest_framework.parsers import MultiPartParser, JSONParser, FormParser
from notifications.utils import create_activity

from django.core.cache import cache


class ProfileAPIViewList(generics.ListAPIView):
    queryset = UserProfile.objects.all()
    filter_backends = [filters.SearchFilter]
    serializer_class = ProfileSerializer
    pagination_class = CustomLimitOffsetPagination
    search_fields = ['username',]    
    

class ProfileDetailAPIView(generics.RetrieveAPIView):
    
    """
    Можно посмотреть профайл пользователя. Только метод get.
    
    """
    
    permission_classes = [IsAuthenticated,]
    serializer_class = ProfileSerializer    
    lookup_field = 'username'
    
    queryset = UserProfile.objects.all()  # Set the queryset to fetch all profiles
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        # Обновление количества подписок
        following_count = Follower.objects.filter(user=instance.user, pending_request=True).count()
        followers_count = Follower.objects.filter(follows=instance.user, pending_request=True).count()
        
        instance.number_of_following = following_count
        instance.number_of_followers = followers_count
        instance.save()

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def get_queryset(self):
        return self.queryset.filter(username=self.kwargs[self.lookup_field])
    

class ProfileAPIView(APIView):    
  
    """
    Модель для вывода и обновления профиля. Ничего в нее передавать не надо, 
    юзер берется из запроса и выводится его личный профиль
    """
    authentication_classes = [JWTAuthentication,]
    permission_classes = [IsAuthenticated,]
    
    @swagger_auto_schema(responses={200: ProfileSerializer})
    def get(self, request):
        user = self.request.user
        profile, created = UserProfile.objects.get_or_create(user=user, username=user.username)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)
    
    @swagger_auto_schema(responses={200: ProfileSerializer})
    def put(self, request):
        user = self.request.user
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=user, username=user.username)
            
        new_username = request.data.get("username")
        
        if new_username != user.username:
            try:                    
                user.username = new_username
                user.save()
            except IntegrityError:
                return Response({"message": "Этот юзернейм уже занят, выберите другой."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        
        if request.data.get("name"):
            profile.name = request.data["name"]
        else:
            profile.name = user.username
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

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
        
        if not password_reset:
                raise APIException(f'Объект PasswordReset с кодом {data["code"]} не найден. Проверьте корректность данных.')

        if int(data['code']) != password_reset.code:
            cot = data['code'] != password_reset.code
            raise APIException(f'Код подтверждения неверен. Проверьте корректность данных. Введенный код: {data["code"]}, {password_reset.code}, {cot}')
        
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
    def post(self, request, user_id, *args, **kwargs):
        data=request.data
        user = User.objects.get(pk=user_id)
        
        serializer = PasswordResetSerializer(data=data)

        if serializer.is_valid():
            print(serializer)
            print(data['new_password'], data['confirm_password'])
            if data['new_password'] != data['confirm_password']:
                return Response({"password": "Password fields didn't match."}, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(data['new_password'])
            user.save()
            
            PasswordReset.objects.get(email=user.email).delete()            

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


class GoogleLoginView(SocialLoginView):
    
    """
    Используется для входа через гугл аккаунт
    """
    
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client
    serializer_class = SocialLoginSerializer
    
    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        return serializer_class(*args, **kwargs)
    
    

class FollowUserView(APIView):
    
    """Можно подписаться и отписаться"""
    
    queryset = Follower.objects.all()
    serializer_class = UserFollowSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        try:
            following_user = User.objects.get(id=pk)
            following_user_profile, _ = UserProfile.objects.get_or_create(user=following_user)
            is_private = following_user_profile.is_private #определяем, профиль приватный или публичный
            follow_user, _ = Follower.objects.get_or_create(user=request.user, follows=following_user)
            if not _:
                follow_user.delete()
                return Response({ "success": True, "message": "unfollowed user" }, status=status.HTTP_204_NO_CONTENT)
            else:
                print(follow_user)
                if not is_private:
                    follow_user.pending_request = True
                    follow_user.save()
                    print(type(following_user))
                    create_activity(user=following_user, event_type='subscription', message=f'Followed by {request.user.username}')
                    return Response({ "success": True, "message": "followed user" }, status=status.HTTP_201_CREATED)
                else:
                    follow_user.pending_request = False
                    follow_user.save()
                    create_activity(following_user, 'subscription_request', f'User {request.user.username} want to follow you')
                    return Response({ "success": True, "message": "request was sent!" }, status=status.HTTP_202_ACCEPTED)
            

        except ObjectDoesNotExist:
            return Response({ "success": False, "message": "following user does not exist" }, status=status.HTTP_404_NOT_FOUND)
    
    
class FollowView(APIView):
    
    """Посмотреть свои подписки"""
    
    queryset = Follower.objects.all()
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):        
        following = Follower.objects.filter(user=request.user, pending_request=True)        
        following_serializer = FollowSerializer(following, many=True)
        return Response({ "success": True, "following": following_serializer.data})


class WhoFollowedByView(APIView):
    
    """Посмотреть подписки юзера с заданным юзернеймом"""
    
    queryset = Follower.objects.all()
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, username):
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"success": False, "message": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)

        following = Follower.objects.filter(user=user, pending_request=True)
        following_serializer = FollowSerializer(following, many=True)

        return Response({"success": True, "following": following_serializer.data})
    
    
class FollowerView(APIView):
    
    """Посмотреть своих подписчиков"""
    
    queryset = Follower.objects.all()
    serializer_class = FollowerSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        followers = Follower.objects.filter(follows=request.user, pending_request=True)
        
        followers_serializer = FollowerSerializer(followers, many=True)
        return Response({ "success": True, "following": followers_serializer.data})


class UsersFollowerView(APIView):
    
    """Посмотреть подписчиков юзера с заданным юзернеймом"""
    
    queryset = Follower.objects.all()
    serializer_class = FollowerSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, username):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({"success": False, "message": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)

        followers = Follower.objects.filter(follows=user, pending_request=True)
        following_serializer = FollowSerializer(followers, many=True)

        followers_serializer = FollowerSerializer(followers, many=True)
        return Response({ "success": True, "following": followers_serializer.data})
    

class RequestUserListView(APIView):
    
    """
    Вью для одобрения подписок от приватного профиля.
    В запрос на одобрение передаем айди профиля (который хочет подписаться),
    и либо accept, либо decline
    
    """
    
    queryset = Follower.objects.all()
    serializer_class = UserFollowSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pending_requests = Follower.objects.filter(follows=request.user, pending_request=False)
        pending_serializer = UserFollowSerializer(pending_requests, many=True)
        
        return Response({ "requests": pending_serializer.data })


class RequestUserView(APIView):
    
    """
    Вью для одобрения подписок от приватного профиля.
    В запрос на одобрение передаем айди профиля (который хочет подписаться),
    и либо accept, либо decline
    
    """
    
    queryset = Follower.objects.all()
    serializer_class = UserFollowSerializer
    permission_classes = [IsAuthenticated]

    def put(self, request, pk=None, action=None):
        try:
            follow_user = User.objects.get(id=pk)
            if follow_user == request.user:
                return Response({"message": "You can't be your own follower"}, status=status.HTTP_400_BAD_REQUEST)
            
            pending_request = Follower.objects.get(follows=request.user, user=follow_user)
            
            if action=='accept':
                pending_request.pending_request=True
                pending_request.save()
                return Response({'status': "accepted"}, status=status.HTTP_200_OK)
            else:
                pending_request.delete()
                print(Follower.objects.filter(follows=request.user, user=follow_user))
                return Response({ "status": "request deleted", "message": "request declined"}, status=status.HTTP_202_ACCEPTED)

        except ObjectDoesNotExist:
            return Response({ "success": False, "message": "following user does not exist"}, status=status.HTTP_400_BAD_REQUEST)



class UserAvatarUpload(viewsets.ModelViewSet):
    
    """Обновить или удалить фото профиля"""
    
    parser_classes = [MultiPartParser, FormParser]
    serializer_class = PhotoProfileSerializer
    queryset = UserProfile.objects.all()
    permission_classes = [IsAuthenticated,]
    
    def get_object(self):
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        user = request.user
        profile = UserProfile.objects.get(user=user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
        
    def update(self, request, *args, **kwargs):
        user = request.user        
        file = request.data['photo']
        profile = UserProfile.objects.get(user=user)
        profile.photo = file
        profile.save()
        return Response("Image updated!", status=status.HTTP_200_OK)
    
    def destroy(self, request, *args, **kwargs):
        user = request.user
        profile = UserProfile.objects.get(user=user)

        if profile.photo:
            profile.photo = None
            profile.save()
            return Response("Image deleted!", status=status.HTTP_204_NO_CONTENT)
        else:
            return Response("No image to delete.", status=status.HTTP_400_BAD_REQUEST)