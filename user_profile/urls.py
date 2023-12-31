from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import (
    ProfileAPIView, 
    UserViewSet, 
    SendPasswordResetEmailView, 
    EnterOTPCodeView,
    UpdatePasswordView,
    RememberMeTokenRefreshView,
    LogoutView,
    ProfileAPIViewList,
    GoogleLoginView,
    FollowUserView,
    RequestUserView,
    FollowView,
    FollowerView,
    RequestUserListView,
    ProfileDetailAPIView,
    WhoFollowedByView,
    UsersFollowerView,
    UserAvatarUpload
    # UserFollowersViewSet,
    # PendingRequestView,
    # FollowUnfollowView
    )

router = DefaultRouter()
# router.register(r'follow', UserFollowersViewSet, basename='user-following')

urlpatterns = [
    path('profile/', ProfileAPIViewList.as_view(), name="profile_list"), #только на время тестирования приложения
    path('me/', ProfileAPIView.as_view(), name='my-profile'),
    path('profile/<str:username>/', ProfileDetailAPIView.as_view(), name="profile"),
    path('register/', UserViewSet.as_view({'post': 'create'}), name='register'),
    path('users/', UserViewSet.as_view({'get': 'list'}), name='user-all'),
    path('users/<int:pk>/', UserViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}), name='user-detail'),
    path('forgot_password/', SendPasswordResetEmailView.as_view(), name="forgot_password"),
    path('otp_verificaton/', EnterOTPCodeView.as_view(), name='verify'),
    path('reset_password/<user_id>/', UpdatePasswordView.as_view(), name='reset-password'),
    path('login/', RememberMeTokenRefreshView.as_view(), name='remember_me'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
    path('google/', GoogleLoginView.as_view(),  name='google'),
    path('follow/', FollowUserView.as_view(), name='follow'),
    path('follow/<int:pk>/', FollowUserView.as_view(), name='follow'),
    path('pending-requests/', RequestUserListView.as_view(), name='requests'),
    path('pending-requests/<int:pk>/<str:action>/', RequestUserView.as_view(), name='accept'),
    path('who-following-by-me/', FollowView.as_view(), name='following'),
    path('who-follow-me/', FollowerView.as_view(), name="follow-me"),
    path('followers/<str:username>/', UsersFollowerView.as_view(), name='followers'),
    path('subscription/<str:username>/', WhoFollowedByView.as_view(), name='follow'),
    path('me/update-profile-photo/', UserAvatarUpload.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='upload-avatar')
    # path('pending-requests/', PendingRequestView.as_view({'get': 'list'}), name='pending-requests'),
    # path('who_follow_me/', UserFollowersViewSet.as_view({'get': 'list'})),
    # path('who_follow_me/<int:follower_id>/', UserFollowersViewSet.as_view({'delete': 'destroy', 'get': 'retrieve',})),
]

urlpatterns += router.urls