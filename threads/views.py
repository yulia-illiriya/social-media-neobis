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
    
    
class CreateThreadView(viewsets.ModelViewSet):
    
    permission_classes = [IsAuthenticated,]
    serializer_class = ThreadSerializer
    queryset = Thread.objects.all()
    
    
class UserThreadList(generics.ListCreateAPIView):
    
    """
    Показать список своих тредов с возможностью опубликовать новый
    """
    
    permission_classes = [IsAuthenticated,]
    serializer_class = ThreadSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = Thread.objects.filter(author=user)
        return queryset
    

class UserThreadListAPIView(generics.ListAPIView):
    
    """Треды выбранного юзера"""
    
    permission_classes = [IsAuthenticated,]
    serializer_class = ThreadSerializer
    queryset = Thread.objects.all()
    
    def get_queryset(self):
        user_pk = self.kwargs['pk']  # Получаем значение pk из URL
        return Thread.objects.filter(user=user_pk)
    

class AllFeedView(generics.ListAPIView):
    
    """
    Возвращает все треды
    """
    
    serializer_class = ThreadSerializer
    
    def get_queryset(self):
        queryset = Thread.objects.exclude(author__userprofile__is_private=True)
        return queryset



