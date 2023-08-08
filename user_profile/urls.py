from django.urls import path
from .views import ProfileAPIView, UserViewSet, send_password_reset_email, enter_otp_code, update_password


urlpatterns = [
    path('profile/', ProfileAPIView.as_view(), name="profile"),
    path('register/', UserViewSet.as_view({'post': 'create'}), name='register'),
    path('users/<int:pk>/', UserViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}), name='user-detail'),
    path('forgot_password/', send_password_reset_email, name="forgot_password"),
    path('otp_verificaton/', enter_otp_code, name='verify'),
    path('reset_password', update_password, name='reset-password')
]