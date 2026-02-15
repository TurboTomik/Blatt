from django.urls import path

from . import views

urlpatterns = [
    path("post/<int:pk>/", views.PostDetailView.as_view(), name="post-detail"),
    path("post/create/", views.PostCreateView.as_view(), name="post-create"),
    path("", views.FeedView.as_view(), name="feed"),
    path("posts/<int:pk>/vote/", views.PostVoteView.as_view(), name="post-vote"),
]
