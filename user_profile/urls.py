from django.urls import path
from .views import (
    ProfileAPIView, 
    UserViewSet, 
    SendPasswordResetEmailView, 
    EnterOTPCodeView,
    UpdatePasswordView,
    RememberMeTokenRefreshView,
    LogoutView
    )



urlpatterns = [
    path('profile/', ProfileAPIView.as_view(), name="profile"),
    path('register/', UserViewSet.as_view({'post': 'create'}), name='register'),
    path('users/<int:pk>/', UserViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}), name='user-detail'),
    path('forgot_password/', SendPasswordResetEmailView.as_view(), name="forgot_password"),
    path('otp_verificaton/', EnterOTPCodeView.as_view(), name='verify'),
    path('reset_password/', UpdatePasswordView.as_view(), name='reset-password'),
    path('login/', RememberMeTokenRefreshView.as_view(), name='remember_me'),
    path('logout/', LogoutView.as_view(), name='auth_logout'),
]