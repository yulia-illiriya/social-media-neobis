from django.urls import path
from threads.views import ThreadView, AllFeedView, CreateThreadView

urlpatterns = [
    path('following-feed/', ThreadView.as_view(), name="following-threads"),
    path('for-you/', AllFeedView.as_view(), name='feed'),
    path('create-thread/', CreateThreadView.as_view(), name='create-thread'),
]
