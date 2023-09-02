from rest_framework import serializers
# from cloudinary_storage.storage import 

from threads.models import Photo, Thread, Like, Quote
from user_profile.serializers import UserSerializer, SimpleProfileSerializer
from cloudinary.uploader import upload


from rest_framework import serializers
from .models import Thread, Photo


class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ('photo',)
        

class ThreadSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    photos=PhotoSerializer(many=True, source='photo_set', required=False)

    class Meta:
        model = Thread
        fields = ('content', 'author', 'video', 'likes', 'created', 'repost', 'photos')
        read_only_fields = ('created', 'likes')

    def create(self, validated_data):
        print(validated_data)
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
    
    
class QuoteSerializer(serializers.ModelSerializer):
    thread = ThreadSerializer(read_only=True)
    who_quoted = serializers.HiddenField(default=serializers.CurrentUserDefault())    
    
    class Meta:
        model = Quote
        fields = ('addional_text', 'thread', 'reposted_at', 'who_quoted')
        
        
class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ["user", "thread"]