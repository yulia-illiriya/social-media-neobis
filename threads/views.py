from django.shortcuts import render
from rest_framework import generics, viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from threads.serializers import ThreadSerializer, PhotoSerializer, QuoteSerializer
from threads.models import Thread, Photo, Quote
from user_profile.models import Follower


class ThreadView(generics.ListAPIView):
    
    """
    Возвращает треды пользователей, на которых подписан юзер
    """
    
    permission_classes = [IsAuthenticated,]
    serializer_class = ThreadSerializer
    
    def get_queryset(self):
        user = self.request.user
        following_authors = Follower.objects.filter(user=user, pending_request=True).values_list('follows', flat=True)
        queryset = Thread.objects.filter(author__in=following_authors)
        return queryset
    

class AllFeedView(generics.ListAPIView):
    
    """
    Возвращает все треды
    """
    
    serializer_class = ThreadSerializer
    queryset = Thread.objects.all()



