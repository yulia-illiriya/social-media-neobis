from django.urls import path, include
from threads.views import ThreadView, AllFeedView, CreateThreadView, UserThreadList, UserThreadListAPIView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'thread', CreateThreadView, basename='thread')


urlpatterns = [
    path('following-feed/', ThreadView.as_view(), name="following-threads"),
    path('for-you/', AllFeedView.as_view(), name='feed'),
    path('create-thread/', CreateThreadView.as_view({'post':'create'}), name='create-thread'),
    path('thread/<int:pk>/', CreateThreadView.as_view({'get':'retrieve', 'delete': 'destroy'}), name='thread'),
    path('user-thread/', UserThreadList.as_view(), name='thread-list'),
    path('user-threads-list/<str:username>/', UserThreadListAPIView.as_view(), name='user-thread-list')
]

