from rest_framework import serializers
# from cloudinary_storage.storage import 

from threads.models import Photo, Thread, Like, Quote
from user_profile.serializers import UserSerializer, SimpleProfileSerializer, UserProfileSerializer
from cloudinary.uploader import upload
from moviepy.editor import VideoFileClip


from rest_framework import serializers
from .models import Thread, Photo, Video


class PhotoSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Photo
        fields = ['photo',]
        
        
class VideoSerializer(serializers.ModelSerializer):
    # video = serializers.FileField()
    class Meta:
        model = Video
        fields = ('video',)
        

class ThreadSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    photos = serializers.SerializerMethodField(required=False)
    
    class Meta:
        model = Thread
        fields = ('id', 'content', 'author', 'likes', 'created', 'photos',)
        read_only_fields = ('created', 'likes')
        
    def get_photos(self, obj):
        photos = Photo.objects.filter(thread=obj)
        print(photos)
        photo_serializer = PhotoSerializer(photos, many=True)
        return photo_serializer.data

    def validate_photos(self, photos):
        if len(photos) > 4:
            raise serializers.ValidationError('Максимум 4 фотографии разрешены')
        return photos
    
   
class ThreadWithVideoSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    videos = VideoSerializer(many=True, required=False)
    # video = serializers.SerializerMethodField(required=False)

    class Meta:
        model = Thread
        fields = ['id', 'content', 'author', 'videos', 'likes', 'created']
        read_only_fields = ('created', 'likes')
    
    # def get_video(self, obj):
    #     request = self.context.get('request')
        
    #     if request and request.method == 'GET':
    #         videos = Video.objects.filter(thread=obj)
    #         video_serializer = VideoSerializer(videos, many=False)
    #         return video_serializer.data
    #     return None
        

class WholeThreadSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()
    photos = PhotoSerializer(many=True, source='photo_set', required=False)
    videos = serializers.SerializerMethodField(required=False)
    
    def get_author(self, obj):
        user_profile = obj.author.userprofile
        user_profile_serializer = UserProfileSerializer(user_profile)
        return user_profile_serializer.data

    def get_videos(self, obj):
        videos = Video.objects.filter(thread=obj)
        video_serializer = VideoSerializer(videos, many=True)
        return video_serializer.data
        
    class Meta:
        model = Thread
        fields = ['id', 'content', 'author', 'likes', 'created', 'photos', 'videos']
        read_only_fields = ('created', 'likes', 'author')
   


class SimpleThreadSerializer(serializers.ModelSerializer):
    
    """Сериалайзер со всеми возможными полями для get-запросов"""
    
    author = serializers.StringRelatedField()
    photos=PhotoSerializer(many=True, source='photo_set', required=False)
    video = VideoSerializer(required=False)    

    class Meta:
        model = Thread
        fields = ('id', 'content', 'author', 'likes', 'created', 'photos', 'video')
        read_only_fields = ('created', 'likes')

    
class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    comments = serializers.PrimaryKeyRelatedField(queryset=Thread.objects.all(), required=False)
    
    class Meta:
        model = Thread
        fields = ('content', 'author', 'video', 'likes', 'created', 'comments', 'photos')
        read_only_fields = ('created', 'likes')
        
        
class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ["user", "thread"]
        
        
class QuoteSerializer(serializers.ModelSerializer):
    thread = ThreadSerializer()
    who_quoted = serializers.StringRelatedField()
    class Meta:
        model = Quote
        fields = [
            "additional_text",
            "thread",
            "created",
            "who_quoted", 
            ]
        
        
class RepostSerializer(serializers.ModelSerializer):
    thread = ThreadSerializer()
    who_quoted = serializers.StringRelatedField()
    class Meta:
        model = Quote
        fields = [
             "thread",
            "created",
            "who_quoted",                       
        ]
