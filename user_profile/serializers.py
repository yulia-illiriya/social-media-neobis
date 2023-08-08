from rest_framework import serializers
from .models import User, UserProfile

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'
        
        
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
    
    new_passsword = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField(min_length=8)