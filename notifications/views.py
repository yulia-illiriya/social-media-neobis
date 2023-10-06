from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.response import Response
from rest_framework import status

from notifications.serializers import ActivitySerializer
from notifications.models import Activity

class ActivityFeed(APIView):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [IsAuthenticated,]

    @swagger_auto_schema(
        operation_description="List of current user activities.",
        responses={
            200: openapi.Response(
                description="List of user activities.",
                schema=ActivitySerializer(many=True),
            ),
            401: "Authentication failed.",
        },
    )
    def get(self, request):
        activities = self.queryset.filter(user=request.user)
        serializer = self.serializer_class(activities, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
