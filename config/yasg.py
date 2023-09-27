from django.urls import path
from rest_framework import permissions
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from drf_yasg.inspectors import SwaggerAutoSchema

schema_view = get_schema_view(
    openapi.Info(
        title="Threads",
        default_version='v1',
        description="API documentation",
        terms_of_service="none",
        contact=openapi.Contact(email="contact@example.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[],
    authentication_classes=[],
)


urlpatterns = [    
    path('swagger/', schema_view.with_ui('swagger'), name='swagger'),
    path('redoc/', schema_view.with_ui('redoc'), name='redoc'),    
]