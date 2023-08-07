from django.shortcuts import render
from rest_framework import generics, viewsets

from user_profile.serializers import ProfileSerializer, UserSerializer
from user_profile.models import UserProfile, User

class ProfileAPIView(generics.RetrieveUpdateAPIView):
    queryset = UserProfile.objects.all()
    serializer_class = ProfileSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

