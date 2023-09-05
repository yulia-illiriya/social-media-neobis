from rest_framework import serializers
# from cloudinary_storage.storage import 

from threads.models import Photo, Thread, Like, Quote
from user_profile.serializers import UserSerializer, SimpleProfileSerializer
from cloudinary.uploader import upload


from rest_framework import serializers
from .models import Thread, Photo, Video


class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ('photo',)
        
        
class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ('video',)
        

class ThreadSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    photos=PhotoSerializer(many=True, source='photo_set', required=False)    

    class Meta:
        model = Thread
        fields = ('id', 'content', 'author', 'likes', 'created', 'photos')
        read_only_fields = ('created', 'likes')

    def create(self, validated_data):
        author = self.context['request'].user
        photos_data = validated_data.pop('photos', [])
        thread = Thread.objects.create(**validated_data, author=author)

        for photo in photos_data:
            Photo.objects.create(thread=thread, **photo)
            
        return thread

    def validate_photos(self, photos):
        if len(photos) > 4:
            raise serializers.ValidationError('Максимум 4 фотографии разрешены')
        return photos
    
    
class ThreadWithVideoSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    video = VideoSerializer(required=False, source="video")

    class Meta:
        model = Thread
        fields = ('id', 'content', 'author', 'video', 'likes', 'created')
        read_only_fields = ('created', 'likes')

    def create(self, validated_data):
        author = self.context['request'].user
        video_data = validated_data.pop('video', [])
        thread = Thread.objects.create(**validated_data, author=author)

        Video.objects.create(thread=thread, **video_data)
            
        return thread


class SimpleThreadSerializer(serializers.ModelSerializer):
    
    """Сериалайзер со всеми возможными полями для get-запросов"""
    
    author = serializers.StringRelatedField()
    photos=PhotoSerializer(many=True, source='photo_set', required=False)
    video = VideoSerializer(required=False, source="video")    

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
