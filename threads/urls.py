from django.urls import path, include
from threads.views import (
    ThreadView, 
    AllFeedView, 
    CreateThreadView, 
    UserThreadList, 
    UserThreadListAPIView, 
    PhotoUploadView,
    LikeView, 
    QuoteViewSet,
    RepostViewSet,
    CommentView,
    ThreadWithCommentsView
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'thread', CreateThreadView, basename='thread')
router.register(r'quote', QuoteViewSet, basename='quote'),
router.register(r'repost', RepostViewSet, basename='repost'),
router.register(r'comment', CommentView, basename='comment')


urlpatterns = [
    path('following-feed/', ThreadView.as_view(), name="following-threads"),
    path('for-you/', AllFeedView.as_view(), name='feed'),
    path('create-thread/', CreateThreadView.as_view({'post':'create'}), name='create-thread'),
    path('thread/<int:pk>/', CreateThreadView.as_view({'get':'retrieve', 'delete': 'destroy'}), name='thread'),
    path('user-thread/', UserThreadList.as_view(), name='thread-list'),
    path('user-threads-list/<str:username>/', UserThreadListAPIView.as_view(), name='user-thread-list'),
    path('upload/', PhotoUploadView.as_view(), name="photo-upload" ),
    path('<int:pk>/like/', LikeView.as_view(), name='like'),
    path('quote/<int:pk>/', QuoteViewSet.as_view({"post": "create", "get": "retrieve", "delete": "destroy"}), name='quote'),
    path('repost/<int:pk>', RepostViewSet.as_view({"post": "create", "get": "retrieve", "delete": "destroy"}), name='repost'),
    path('comment/<int:parent_thread_id>/', CommentView.as_view({"post": "create", "get": "retrieve", "delete": "destroy"}), name='add-comment'),
    path('thread/thread-with-comments/<int:thread_pk>/', ThreadWithCommentsView.as_view({'get': 'retrieve'}), name="thread-with-comments")
]

