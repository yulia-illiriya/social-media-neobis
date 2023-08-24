from rest_framework import serializers

from threads.models import Photo, Thread, Like, Quote
from user_profile.serializers import UserSerializer, SimpleProfileSerializer


class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ('photo',)        
         

class ThreadSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    photo = PhotoSerializer(many=True, read_only=True, source='photo_set')
    
    class Meta:
        model = Thread
        fields = ("content", "author", "photo", "video", "created", "likes")
        
    def create(self, validated_data):
        
        author = self.context['request'].user
        # Проверка на количество фото (не больше четырех)
        if "photo":            
            photos_data = validated_data.pop('photo', [])
            if len(photos_data) > 4:
                raise serializers.ValidationError("Максимум 4 фотографии разрешены")
            for photo_data in photos_data:
                Photo.objects.create(thread=thread, **photo_data)

        thread = Thread.objects.create(author=author, **validated_data)

        return thread
    
    
class QuoteSerializer(serializers.ModelSerializer):
    thread = ThreadSerializer(read_only=True)
    who_quoted = serializers.HiddenField(read_only=True, default=serializers.CurrentUserDefault())    
    
    class Meta:
        model = Quote
        fields = ('addional_text', 'thread', 'reposted_at', 'who_quoted')
        
        
class Like(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ["user",]