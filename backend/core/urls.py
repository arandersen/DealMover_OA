from django.urls import path
from .views import health, extract_view

urlpatterns = [
    path("health", health),          # GET /api/health
    path("extract/", extract_view),  # POST /api/extract/
]