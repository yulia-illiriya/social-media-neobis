from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework import generics, viewsets, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from cloudinary.uploader import upload
from moviepy.editor import VideoFileClip
import os
import tempfile
import sys

from threads.serializers import (
    ThreadSerializer, 
    ThreadWithVideoSerializer,
    PhotoSerializer, 
    QuoteSerializer, 
    LikeSerializer, 
    RepostSerializer, 
    CommentSerializer, 
    SimpleThreadSerializer,
    VideoSerializer,
    WholeThreadSerializer
)
from threads.models import Thread, Photo, Quote, Like, User, Video
from user_profile.models import Follower
from user_profile.permissions import CanAccessPrivateThreads
from notifications.utils import create_activity
from threads.permissions import IsOwnerOrReadOnly
from threads.utils import compress_and_upload_video, compress_and_upload_image
from cloudinary.uploader import upload

from rest_framework.parsers import MultiPartParser, JSONParser, FormParser
import cloudinary.uploader
from django.db.models import F
from itertools import chain


class ThreadView(generics.ListAPIView):
    
    """
    Возвращает треды пользователей, на которых подписан юзер
    """
    
    permission_classes = [IsAuthenticated,]
    serializer_class = SimpleThreadSerializer
    
    def get_queryset(self):
        user = self.request.user
        following_authors = Follower.objects.filter(user=user, pending_request=True).values_list('follows', flat=True)
        queryset = Thread.objects.filter(author__in=following_authors)        
        
        return queryset
   
 
    
class CreateThreadView(viewsets.ModelViewSet):
    
    """создает тред"""
    
    permission_classes = [IsAuthenticated,]
    queryset = Thread.objects.all()
    
    parser_classes = (
        MultiPartParser,
        JSONParser,
        FormParser
    )
    
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return WholeThreadSerializer
        elif 'photos' in self.request.data:
            return ThreadSerializer
        elif 'videos' in self.request.data:
            return ThreadWithVideoSerializer
        else:
            return WholeThreadSerializer
        
    def create(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, context={'request': request})
        print(request.data)
        serializer.is_valid(raise_exception=True)
        print(serializer)
        serializer.validated_data['author'] = request.user
        thread = serializer.save()
        video_file = request.data.get('videos')
        photos = request.FILES.getlist("photos")
        
        print(video_file)
        
        if request.FILES:            
            if video_file and photos:
                return Response(
                    {"message": "You cannot upload video and photos in one time. Choose only photo or video"}, 
                    status=status.HTTP_406_NOT_ACCEPTABLE
                    )
            elif video_file:            
                video_size = sys.getsizeof(video_file.read())
                video_file.seek(0)

                if video_size <= 2.5 * 1024 * 1024:                
                    video_url = upload(video_file, resource_type='video')
                    videodata = video_url.get('playback_url')
                else:
                    videodata = compress_and_upload_video(video_file)
                Video.objects.create(video=videodata, thread=thread)            
            else:
                for photo in photos:
                    photo_url = compress_and_upload_image(photo)
                    print(photo_url)
                    pho = Photo.objects.create(thread=thread, photo=photo_url)
                    print(pho.thread, pho.photo)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class PhotoUploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        print(request.data)
        
        # Преобразуем строку thread_id в целое число
        thread_id = int(request.data["thread_id"])

        # Создаем словарь данных для сериализации
        data = {'photo': request.data["photo"], 'thread_id': thread_id}
        serializer = PhotoSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class VideoUploadView(APIView):
    permission_classes = [IsAuthenticated,]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        video_file = request.data['video']
        video_size = sys.getsizeof(video_file.read())
        video_file.seek(0)  # Возвращаем указатель на начало файла
        # Сжимаем видео и загружаем его в Cloudinary
        if video_size <= 2.5 * 1024 * 1024:
            video_url = upload(video_file, resource_type='video')
            compressed_video_url = video_url.get('playback_url')
        else:
            compressed_video_url = compress_and_upload_video(video_file)

        return Response({'compressed_video_url': compressed_video_url}, status=status.HTTP_201_CREATED)

        
    
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
        return Thread.objects.filter(author__username=username)
    

# class AllFeedView(APIView):
    
#     """
#     лента всех тредов, включая репосты и цитаты.
#     не включены авторы с приватным профилем
#     """
    
#     def get(self, request, *args, **kwags):
#         threads = Thread.objects.filter(comment=None, author__userprofile__is_private=False)
#         quotes = Quote.objects.filter(
#             Q(who_quoted__userprofile__is_private=False) & Q(is_repost=False)
#         )
#         reposts = Quote.objects.filter(is_repost=True)

#         thread_serializer = WholeThreadSerializer(threads, many=True)
#         quote_serializer = QuoteSerializer(quotes, many=True)
#         repost_serializer = RepostSerializer(reposts, many=True)

#         response_data = {
#             "threads": thread_serializer.data,
#             "quotes": quote_serializer.data,
#             "reposts": repost_serializer.data,
#         }

#         return Response(response_data, status=status.HTTP_200_OK)



class AllFeedView(APIView):
    """
    лента всех тредов, включая репосты и цитаты.
    не включены авторы с приватным профилем
    """
    
    def get(self, request, *args, **kwags):
        threads = Thread.objects.filter(comment=None, author__userprofile__is_private=False)
        quotes = Quote.objects.filter(
            Q(who_quoted__userprofile__is_private=False) & Q(is_repost=False)
        )
        reposts = Quote.objects.filter(is_repost=True)

        all_items = list(chain(threads, quotes, reposts))        
        
        sorted_items = sorted(all_items, key=lambda item: item.created, reverse=True)

        serialized_items = []
        for item in sorted_items:
            if isinstance(item, Thread):
                serialized_items.append(WholeThreadSerializer(item).data)
            elif isinstance(item, Quote) and not item.is_repost:
                serialized_items.append(QuoteSerializer(item).data)
            elif isinstance(item, Quote) and item.is_repost:
                serialized_items.append(RepostSerializer(item).data)

        return Response(serialized_items, status=status.HTTP_200_OK)
    

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
                thread.likes -= 1
                thread.save()
                return Response({ "success": True, "message": "unlike thread" }, status=status.HTTP_201_CREATED)
            else:
                thread.likes += 1
                thread.save()
                create_activity(user=thread.author, event_type='post_like', message=f'{request.user} liked your thread {thread.pk}')                    
                return Response({ "success": True, "message": "like thread" }, status=status.HTTP_201_CREATED)
            
        except ObjectDoesNotExist:
            return Response({ "success": False, "message": "user ot thread doesn't exist" })
        
        
        
class QuoteViewSet(viewsets.ModelViewSet):
    
    """
    можно передать дополнительный текст
    """
    
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    queryset = Quote.objects.all()
    serializer_class = QuoteSerializer
    
    def create(self, request, pk, *args, **kwargs):
        try:
            who_added = request.user
            thread = Thread.objects.get(pk=pk)
            is_repost = False
            additional_text = request.data.get('additional_text')            
            quote, _ = Quote.objects.get_or_create(who_quoted=who_added, thread=thread, is_repost=is_repost, additional_text=additional_text)           
            
            if not _:
                return Response({"success": False, "message": "you've already reposted it"})  
            
            serializer = QuoteSerializer(quote)
            
            return Response({"success": True, "message": "quote is created"}, status=status.HTTP_201_CREATED)         
            
        except ObjectDoesNotExist:
            return Response({ "success": False, "message": "user ot thread doesn't exist" }, status=status.HTTP_404_NOT_FOUND)


class RepostViewSet(viewsets.ModelViewSet):
    
    """
    в эндпойнт надо передать id треда, который репостим.
    больше ничего передавать не надо.
    создается репост
    
    """
    
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    queryset = Quote.objects.all()
    serializer_class = RepostSerializer
    
    def create(self, request, pk, *args, **kwargs):
        try:
            who_added = request.user
            thread = Thread.objects.get(pk=pk)
            is_repost = True                   
            quote, _ = Quote.objects.get_or_create(who_added=who_added, thread=thread, is_repost=is_repost)           
            
            if not _:
                return Response({"success": False, "message": "you've already reposted it"})  
            
            serializer = RepostSerializer(quote)
            
            return Response({"success": True, "message": "you reposted it successfully!"}, status=status.HTTP_201_CREATED)         
            
        except ObjectDoesNotExist:
            return Response({ "success": False, "message": "user ot thread doesn't exist" }, status=status.HTTP_404_NOT_FOUND)
        
        
class CommentView(viewsets.ModelViewSet):
    
    """
    Можно посмотреть комментарий, добавить, но надо передавать id треда, который комментируем.
    Удалить тоже можно. 
    """
    
    permission_classes = [IsAuthenticated,]
    serializer_class = ThreadSerializer
    queryset = Thread.objects.all()    
    
    def create(self, request, parent_thread_id, *args, **kwargs):
        author = request.user        
        
        photos_data = request.data.get('photos', [])

        try:
            parent_thread = Thread.objects.get(pk=parent_thread_id)
        except ObjectDoesNotExist:
            return Response({ "success": False, "message": "user ot thread doesn't exist" }, status=status.HTTP_404_NOT_FOUND)        

        thread = Thread.objects.create(author=author, comment=parent_thread, **request.data)
        
        if photos_data:                
            for photo in photos_data:
                Photo.objects.create(thread=thread, **photo)

        serializer = ThreadSerializer(thread)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    


class ThreadWithCommentsView(viewsets.ReadOnlyModelViewSet):
    serializer_class = ThreadSerializer
    queryset = Thread.objects.all()

    def retrieve(self, request, thread_pk):
        instance = Thread.objects.get(pk=thread_pk)        

        # Получаем все комментарии, связанные с этим тредом
        comments = Thread.objects.filter(comment=instance)

        # Сериализуем их
        serializer = self.get_serializer(comments, many=True)

        # Сериализуем сам тред
        instance_serializer = self.get_serializer(instance)

        # Создаем объект ответа, который включает сам тред и его комментарии
        data = {
            "thread": instance_serializer.data,
            "comments": serializer.data
        }

        return Response(data)