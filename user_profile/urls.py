from django.urls import path
from .views import ProfileAPIView, UserViewSet
from .services import send_email_verification, verify

urlpatterns = [
    path('profile/', ProfileAPIView.as_view(), name="profile"),
    path('register/', UserViewSet.as_view({'post': 'create'}), name='register'),
    path('users/<int:pk>/', UserViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update'}), name='user-detail'),
    path('send_email_verification/', send_email_verification),
    path('verify/', verify, name='verify')
]