from rest_framework import serializers
from notifications.models import Activity

class ActivitySerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Activity
        fields = ['message']