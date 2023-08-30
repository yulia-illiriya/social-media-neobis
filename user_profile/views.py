import random
from datetime import timedelta, timezone
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.urls import reverse
from django.core.exceptions import ObjectDoesNotExist

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
                                    FollowSerializer
                                    )
from user_profile.models import UserProfile, User, PasswordReset, Follower
from config import settings

from django.core.cache import cache


class ProfileAPIViewList(generics.ListAPIView):
    queryset = UserProfile.objects.all()
    filter_backends = [filters.SearchFilter]
    serializer_class = ProfileSerializer
    search_fields = ['username',]    
    

class ProfileDetailAPIView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated,]
    serializer_class = ProfileSerializer
    lookup_field = 'username'
    
    queryset = UserProfile.objects.all()  # Set the queryset to fetch all profiles

    def get_queryset(self):
        return self.queryset.filter(username=self.kwargs[self.lookup_field])

class ProfileAPIView(APIView):
    
    """
    Модель для вывода и обновления профиля. Ничего в нее передавать не надо, 
    юзер берется из запроса и выводится его личный профиль
    """
    
    def get(self, request):
        user = self.request.user
        profile, created = UserProfile.objects.get_or_create(user=user, username=user.username)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)
    
    def put(self, request):
        user = self.request.user
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            UserProfile.objects.create(user=user, username=user.username) 
        serializer = ProfileSerializer(profile, data=request.data)
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
    
    """Можно подписаться и отписаться, а также посмотреть список активных подписок"""
    
    queryset = Follower.objects.all()
    serializer_class = UserFollowSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        following = Follower.objects.filter(user=request.user, pending_request=True)
        followers = Follower.objects.filter(follows=request.user, pending_request=True)

        following_serializer = UserFollowSerializer(following, many=True)
        followers_serializer = UserFollowSerializer(followers, many=True)
        return Response({ "success": True, "following": following_serializer.data, "followers": followers_serializer.data })


    def post(self, request, pk):
        try:
            following_user = User.objects.get(id=pk)
            is_private = following_user.userprofile.is_private #определяем, профиль приватный или публичный
            follow_user, _ = Follower.objects.get_or_create(user=request.user, follows=following_user)
            if not _:
                follow_user.delete()
                return Response({ "success": True, "message": "unfollowed user" })
            else:
                print(follow_user)
                if not is_private:
                    follow_user.pending_request = True
                    follow_user.save()
                    return Response({ "success": True, "message": "followed user" })
                else:
                    follow_user.pending_request = False
                    follow_user.save()
                    return Response({ "success": True, "message": "request was sent!" })


        except ObjectDoesNotExist:
            return Response({ "success": False, "message": "following user does not exist" })
    
    
class FollowView(APIView):
    
    """Посмотреть свои подписки"""
    
    queryset = Follower.objects.all()
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        following = Follower.objects.filter(user=request.user, pending_request=True)
        # followers = Follower.objects.filter(follows=request.user, pending_request=True)

        following_serializer = FollowSerializer(following, many=True)
        # followers_serializer = UserFollowSerializer(followers, many=True)
        return Response({ "success": True, "following": following_serializer.data})
    

class FollowerView(APIView):
    
    """Посмотреть своих подписчиков"""
    
    queryset = Follower.objects.all()
    serializer_class = FollowerSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        followers = Follower.objects.filter(follows=request.user, pending_request=True)
        
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
                return Response({ "status": "request deleted", "message": "request declined" })

        except ObjectDoesNotExist:
            return Response({ "success": False, "message": "following user does not exist" })


# class FollowUnfollowView(viewsets.ModelViewSet):
    
#     """Вью для добавления подписок"""

#     permission_classes = (IsAuthenticatedOrReadOnly,)
#     serializer_class = FollowerSerializer
#     queryset = Follower.objects.all()    
    
    # def list(self):
    #     serializer = FollowerSerializer
    #     queryset = Follower.objects.all()  
    #     return Response(serializer.data)  
   

# class PendingRequestViewSet(APIView):
    
#     """
#     Вью для одобрения или отклонения запросов на подписку
#     """    
#     # permission_classes = (IsAuthenticated,)

#     def list(self, request):
#         user = self.request.user
#         follower_profiles = UserProfile.objects.filter(user__followed__followers__user=user, followers__pending_request=False)     
#         serialized_profiles = SimpleProfileSerializer(follower_profiles, many=True)
#         return Response(serialized_profiles.data)

#     def accept(self, request, pk=None):
#         try:
#             pending_request = Follower.objects.get(pk=pk, followed_user=request.user, pending_request=False)
#             pending_request.pending_request = True
#             pending_request.save()
#             return Response({"message": "Request accepted"}, status=status.HTTP_200_OK)
#         except Follower.DoesNotExist:
#             return Response({"error": "Pending request not found"}, status=status.HTTP_404_NOT_FOUND)

#     def decline(self, request, pk=None):
#         try:
#             pending_request = Follower.objects.get(pk=pk, followed_user=request.user, pending_request=False)
#             pending_request.delete()
#             return Response({"message": "Request declined"}, status=status.HTTP_204_NO_CONTENT)
#         except Follower.DoesNotExist:
#             return Response({"error": "Pending request not found"}, status=status.HTTP_404_NOT_FOUND)
        
        
# class DeclineRequestView(generics.DestroyAPIView):
#     queryset = Follower.objects.all()
#     serializer_class = FollowerSerializer

# class PendingRequestView(viewsets.ViewSet):
#     """
#     Вью для просмотра заявок на подписку для приватных профилей.
#     В метод update передаем дополнительно id
#     """
    
#     serializer_class = SimpleProfileSerializer
#     permission_classes = [IsAuthenticated]
    
#     def list(self, request):
#         user_profile = UserProfile.objects.get(user=request.user)
#         if user_profile.is_private:
#             who_want_to_follow = UserProfile.objects.filter(
#                 user__followed__followers=request.user,
#                 user__followed__pending_request=False
#             )
#             serialized_profiles = self.serializer_class(who_want_to_follow, many=True)
#             return Response(serialized_profiles.data)
#         else:
#             return Response([])
        
#     def update(self, request, follower_id):        
        
#         user_profile = UserProfile.objects.get(user=request.user)
#         follower = Follower.objects.get(followed_user_id=follower_id, followers=user_profile.user)
#         follower.pending_request = True
#         follower.save()
#         return Response({"message": "Request accepted."})


# class UserFollowersViewSet(viewsets.ViewSet):
    
#     """
#     Вью для просмотра тех, кто подписан на юзера. Смотрим только свои подписки!
#     Юзер берется из реквеста
    
#     """
    
#     serializer_class = SimpleProfileSerializer
#     permission_classes = [IsAuthenticated,]  # Только аутентифицированные пользователи
    

#     def get_queryset(self):
#         user_profile = UserProfile.objects.get(user=self.request.user)
#         return UserProfile.objects.filter(
#                 user__followed__followers=self.request.user,
#                 user__followed__pending_request=True
#             )
        
#     def retrieve(self, request, follower_id, *args, **kwargs):
#         try:
#             user_profile = UserProfile.objects.get(user=request.user)
#             follower = Follower.objects.get(followed_user_id=follower_id, followers=user_profile.user)
#             serialized_follower = self.serializer_class(follower)
#             return Response(serialized_follower.data)
#         except Follower.DoesNotExist:
#             return Response({"message": "Follower not found."}, status=status.HTTP_404_NOT_FOUND)
            

#     def destroy(self, request, follower_id, *args, **kwargs):
#         try:
#             user_profile = UserProfile.objects.get(user=request.user)
#             follower = Follower.objects.get(followed_user_id=follower_id, followers=user_profile.user)
#             follower.delete()
#             return Response(status=status.HTTP_204_NO_CONTENT)
#         except Follower.DoesNotExist:
#             return Response({"message": "Follower not found."}, status=status.HTTP_404_NOT_FOUND)
    
# class UserFollowersView(APIView):
    
#     def get(self, request):
#         user = self.request.user
#         user_profile = UserProfile.objects.get(user=request.user)   
        
#         who_follows = UserProfile.objects.filter(
#                 user__followed__followers=user, 
#                 user__followed__pending_request=True
#                 )
#         serialized_profiles = SimpleProfileSerializer(who_follows, many=True)
#         if user_profile.is_private == False:            
#                 return Response(serialized_profiles.data)
#         else:
#             who_want_to_follow = UserProfile.objects.filter(
#                 user__followed__followers=user, 
#                 user__followed__pending_request=False
#                 )
        

    
    
    
#     # .annotate(
#     #         has_pending_request=Case(
#     #             When(user__followed_by__followers__pending_request=True, then=Value(True)),
#     #             default=Value(False),
#     #             output_field=BooleanField()
    