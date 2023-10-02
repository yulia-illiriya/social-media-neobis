from rest_framework import serializers
# from cloudinary_storage.storage import 

from threads.models import Photo, Thread, Like, Quote
from user_profile.serializers import UserSerializer, SimpleProfileSerializer
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
    author = serializers.StringRelatedField()
    photos = PhotoSerializer(many=True, source='photo_set', required=False)
    videos = serializers.SerializerMethodField(required=False)

    def get_videos(self, obj):
        videos = Video.objects.filter(thread=obj)
        print(videos)
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

    # def create(self, validated_data):
    #     print(validated_data)
    #     author = self.context['request'].user
    #     photos_data = validated_data.pop('photos', [])
    #     comments = validated_data.pop('comments')
    #     thread = Thread.objects.create(**validated_data, author=author, comment=comments)

    #     for photo in photos_data:
    #         Photo.objects.create(thread=thread, **photo)
            
    #     return thread

# class PhotoSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Photo
#         fields = ('photo',)        
         

# class ThreadSerializer(serializers.ModelSerializer):
#     author = serializers.StringRelatedField()
#     photo = PhotoSerializer(many=True, source="photo_set")
#     likes = serializers.ReadOnlyField()
    
#     class Meta:
#         model = Thread
#         fields = ["content", "author", "photo", "video", "created", "likes"]
#         ordering = ["-created"]
        
        
#     def create(self, validated_data):
#         author = self.context['request'].user
#         photos = self.initial_data.get('photo', [])
#         thread = Thread.objects.create(author=author, **validated_data)
#         for photo in photos:
#             Photo.objects.create(photo=photo, thread=thread)     
     
#         return thread
    

    
    # def create(self, validated_data, photo):
    #     print(validated_data, )
        
    #     
    #     # Проверка на количество фото (не больше четырех)
    #     if "photo":
    #         print(True)            
    #         photos_data = validated_data.pop('photo')
    #         if len(photos_data) > 4:
    #             raise serializers.ValidationError("Максимум 4 фотографии разрешены")
    #         for photo_data in photos_data:
    #             Photo.objects.create(thread=thread, **photo_data)

    #     thread = Thread.objects.create(author=author, **validated_data)

    #     return thread
    
    
# class QuoteSerializer(serializers.ModelSerializer):
#     thread = ThreadSerializer(read_only=True)
#     who_quoted = serializers.HiddenField(default=serializers.CurrentUserDefault())    
    
#     class Meta:
#         model = Quote
#         fields = ('addional_text', 'thread', 'reposted_at', 'who_quoted')
        
        
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
            "reposted_at",
            "who_quoted", 
            ]
        
        
class RepostSerializer(serializers.ModelSerializer):
    thread = ThreadSerializer()
    who_quoted = serializers.StringRelatedField()
    class Meta:
        model = Quote
        fields = [
             "thread",
            "reposted_at",
            "who_quoted",                       
        ]
