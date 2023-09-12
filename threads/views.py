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

from threads.serializers import (
    ThreadSerializer, 
    ThreadWithVideoSerializer,
    PhotoSerializer, 
    QuoteSerializer, 
    LikeSerializer, 
    RepostSerializer, 
    CommentSerializer, 
    SimpleThreadSerializer,
    VideoSerializer
)
from threads.models import Thread, Photo, Quote, Like, User, Video
from user_profile.models import Follower
from user_profile.permissions import CanAccessPrivateThreads
from threads.permissions import IsOwnerOrReadOnly
from threads.utils import compress_and_upload_video, compress_and_upload_image

from rest_framework.parsers import MultiPartParser, JSONParser, FormParser
import cloudinary.uploader


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
        # Проверяем наличие фото и видео в запросе
        if 'photos' in self.request.data:
            return ThreadSerializer
        elif 'videodata' in self.request.data:
            return ThreadWithVideoSerializer
        else:
            return ThreadSerializer
        
    def create(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, context={'request': request})
        print(request.user)
        print(request.data)
        serializer.is_valid(raise_exception=True)
        print(serializer)
        thread = serializer.save()
        
        video_file = request.data.get('videodata')
        photos = request.data.get('photos')
        
        if video_file:
            videodata = compress_and_upload_video(video_file)
            print(videodata)
            
        if photos:
            new_photos = []
            for photo in photos:
                photo_url = compress_and_upload_image(photo)
                new_photos.append(photo_url)
            photos = new_photos
        
        serializer.save()
            
        print(serializer.data)      

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
    

# def compress_and_upload_video(video_file):
#     temp_video_dir = tempfile.mkdtemp()
#     # Указываем путь к загруженному видео файлу
    
#     # Сжимаем видео
#     input_path = video_file.temporary_file_path()
#     compressed_video_path = os.path.join(temp_video_dir, "compressed_video.mp4")
#     # Сжимаем видео
#     video_clip = VideoFileClip(input_path)
#     compressed_clip = video_clip.resize(width=640)  # Пример сжатия до ширины 640 пикселей, можно настроить как вам нужно
    
#     compressed_clip.write_videofile(compressed_video_path, codec="libx264")
    
#     # Загружаем сжатое видео в Cloudinary
#     compressed_video_upload = upload(compressed_video_path, resource_type="video")

#     # Получаем URL загруженного сжатого видео из Cloudinary
#     video_url = compressed_video_upload["secure_url"]
#     os.remove(compressed_video_path)

#     return video_url


class VideoUploadView(APIView):
    permission_classes = [IsAuthenticated,]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, format=None):
        video_file = request.data['video']

        # Сжимаем видео и загружаем его в Cloudinary
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
        return Thread.objects.filter(user__username=username)
    

# class AllFeedView(generics.ListAPIView):
    
#     """
#     Возвращает все треды
#     """
    
#     serializer_class = ThreadSerializer
    
#     def get_queryset(self):
#         queryset = Thread.objects.exclude(author__userprofile__is_private=True)
#         return queryset


class AllFeedView(generics.ListAPIView):
    
    """
    лента всех тредов, включая репосты и цитаты.
    не включены авторы с приватным профилем
    """
    swagger_fake_view = True
    @swagger_auto_schema(operation_description="Метода GET",
        manual_parameters=[],
        responses={status.HTTP_200_OK: openapi.Response('Описание успешного ответа', example={
                    "threads": [SimpleThreadSerializer],
                    "quotes": [QuoteSerializer],
                    "reposts": [RepostSerializer]
                })},) 
    def list(self, request, *args, **kwags):
        
        threads = Thread.objects.filter(comment=None, author__userprofile__is_private=False)

        quotes = Quote.objects.filter(       
            Q(who_quoted__userprofile__is_private=False) & Q(is_repost=False)
        )
        
        reposts = Quote.objects.filter(is_repost=True)
    
        thread_serializer = ThreadSerializer(threads, many=True)
        quote_serializer = QuoteSerializer(quotes, many=True)
        reposts = RepostSerializer(reposts, many=True)

        combined_data = thread_serializer.data + quote_serializer.data + reposts.data

        return Response(combined_data, status=status.HTTP_200_OK)
    

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
                return Response({ "success": True, "message": "unlike thread" })
            else:
                thread.likes += 1
                thread.save()                         
                return Response({ "success": True, "message": "like thread" })
            
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