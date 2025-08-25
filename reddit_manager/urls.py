from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render

# Home page view
def home(request):
    return render(request, "base.html")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", home, name="home"),  # Root URL

    # Users app routes
    path("users/", include("users.urls")),

    # Posts app routes
    path("posts/", include("posts.urls")),
]
