from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, UserProfile, Follower
from config import settings
from rest_framework.exceptions import ValidationError
from django.core.files.images import get_image_dimensions


    

class ProfileSerializer(serializers.ModelSerializer):
    number_of_followers = serializers.ReadOnlyField()
    photo = serializers.ImageField(required=False, allow_null=True)
    
    def validate_photo(self, photo):
        if photo:
            filesize = photo.size    

            if filesize > 15 * 1024 * 1024:
                raise ValidationError(f"Размер файла не должен превышать 15 Мб")
        
        return photo
    
    class Meta:
        model = UserProfile
        fields = ['user', 'username', 'name', 'photo', 'bio', 'is_private', 'number_of_followers', 'number_of_following']
        
        
class SimpleProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['username', 'name', 'photo',]
        

class PhotoProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['photo',]
        
        
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User        
        fields = ['email', 'username', 'password', 'confirm_password']
        
    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Пароли не совпадают")
        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            username=validated_data['username']
        )
        return user
   
    
    
class PasswordResetEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    

class OTPSerializer(serializers.Serializer):    
    code = serializers.RegexField(r'^\d{4}$')
    

class PasswordResetSerializer(serializers.Serializer):
    
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField(min_length=8)
    
    class Meta:
        model = User
        fields = ('new_password', 'confirm_password')
    
    
class RememberMeTokenObtainPairSerializer(TokenObtainPairSerializer):
    remember_me = serializers.BooleanField(required=False)

    def validate(self, attrs):
        data = super().validate(attrs)
        if self.initial_data.get('remember_me'):
            user = self.user
            user.remember_me = True
            user.save()
        return data



class UserFollowSerializer(serializers.ModelSerializer):
    follows = serializers.CharField(source='follows.username')
    follower = serializers.CharField(source='user.username')
    class Meta:
        model = Follower
        fields = [ "pending_request", "created_at", "follows", 'follower']
        

class FollowSerializer(serializers.ModelSerializer):
    follows = serializers.CharField(source='follows.username')
    class Meta:
        model = Follower
        fields = [ "follows",]
        
        
class FollowerSerializer(serializers.ModelSerializer):
    followers = serializers.CharField(source='user.username')
    class Meta:
        model = Follower
        fields = [ "followers",]

   
# class FollowerSerializer(serializers.ModelSerializer):
#     followers = serializers.IntegerField()
    
#     class Meta:
#         model = Follower
#         fields = ("followers", "created_at")
        
#     def create(self, validated_data):
#         followers = validated_data.get('followers')
#         user = self.context['request'].user

#         pending_request = False if UserProfile.objects.get(user=followers).is_private else True

#         follower_data = {
#             'followed_user': user,
#             'followers': followers,
#             'pending_request': pending_request
#         }
        
#         return Follower.objects.create(**follower_data)


        
        
# class FollowingSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Follower
#         fields = ("followers", "created_at")
        
        
# class ProfileFollowSerializer(serializers.ModelSerializer):
    
#     followers = serializers.SerializerMethodField()
    
#     def get_followers(self, obj):
#         return FollowerSerializer(obj.followed.all(), many=True).data
    
#     class Meta:
#         model = UserProfile
#         fields = ['followers',]
        
        
# class ProfileSubscriptionSerializer(serializers.ModelSerializer):
    
#     following = serializers.SerializerMethodField()
    
#     def get_following(self, obj):
#         return FollowerSerializer(obj.followers.all(), many=True).data
    
#     class Meta:
#         model = UserProfile
#         fields = ['following',]
        
        
# class PendingRequestSerializer(serializers.Serializer):
#     pending_request = serializers.CharField()
#     potential_followers = 