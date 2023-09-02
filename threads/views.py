from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import generics, viewsets, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from threads.serializers import ThreadSerializer, PhotoSerializer, QuoteSerializer, LikeSerializer
from threads.models import Thread, Photo, Quote, Like, User
from user_profile.models import Follower
from user_profile.permissions import CanAccessPrivateThreads

from rest_framework.parsers import MultiPartParser, JSONParser, FormParser
import cloudinary.uploader


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
    
    """создает тред"""
    
    permission_classes = [IsAuthenticated,]
    serializer_class = ThreadSerializer
    queryset = Thread.objects.all()
    
    parser_classes = (
        MultiPartParser,
        JSONParser,
    )


class PhotoUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        serializer = PhotoSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # @staticmethod
    # def post(request):
    #     photos = request.data.get('photos')

    #     for photo in photos:
    #         photos_data = cloudinary.uploader.upload(photo)
    #         return Response({
    #             'status': 'success',
    #             'data': photos_data,
    #         }, status=201)
    
    
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
    
    """
    Треды выбранного юзера.
    Требуется аутентификация и подписка, если юзер приватный.
    
    """
    
    permission_classes = [IsAuthenticated, CanAccessPrivateThreads]
    serializer_class = ThreadSerializer
    queryset = Thread.objects.all()
    
    def get_queryset(self):
        username = self.kwargs['username']  # Получаем значение username из URL
        return Thread.objects.filter(user__username=username)
    

class AllFeedView(generics.ListAPIView):
    
    """
    Возвращает все треды
    """
    
    serializer_class = ThreadSerializer
    
    def get_queryset(self):
        queryset = Thread.objects.exclude(author__userprofile__is_private=True)
        return queryset


class LikeView(APIView):   
    
    """Если лайк существует, то он удаляется, 
    если нет - создается"""
     
    class Meta:
        serializer_class = LikeSerializer
        queryset = Like.objects.all()
    
    def post(self, request, pk):
        try:
            user = request.user
            thread = Thread.objects.get(pk=pk)
            like, _ = Like.objects.get_or_create(user=request.user, thread=thread)
            if not _:
                like.delete()
                return Response({ "success": True, "message": "unlike thread" })
            else:                         
                return Response({ "success": True, "message": "followed user" })
            
        except ObjectDoesNotExist:
            return Response({ "success": False, "message": "user ot thread doesn't exist" })

