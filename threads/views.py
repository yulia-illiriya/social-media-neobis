from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import generics, viewsets, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from threads.serializers import (
    ThreadSerializer, 
    ThreadWithVideoSerializer,
    PhotoSerializer, 
    QuoteSerializer, 
    LikeSerializer, 
    RepostSerializer, 
    CommentSerializer, 
    SimpleThreadSerializer
)
from threads.models import Thread, Photo, Quote, Like, User
from user_profile.models import Follower
from user_profile.permissions import CanAccessPrivateThreads
from threads.permissions import IsOwnerOrReadOnly

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
    )
    
    def get_serializer_class(self):
        # Проверяем наличие фото и видео в запросе
        if 'photos' in self.request.data:
            return ThreadSerializer
        elif 'video' in self.request.data:
            return ThreadWithVideoSerializer
        else:
            return ThreadSerializer


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
    
    def list(self, request, *args, **kwags):
        
        threads = Thread.objects.filter(comment=None, author__userprofile__is_private=False)

        quotes = Quote.objects.filter(       
            who_quoted__userprofile__is_private=False
        )
    
        thread_serializer = ThreadSerializer(threads, many=True)
        quote_serializer = QuoteSerializer(quotes, many=True)

        combined_data = thread_serializer.data + quote_serializer.data

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