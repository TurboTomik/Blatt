from django.urls import include, path

from . import views

urlpatterns = [
    path("create/", views.CreateCommunityView.as_view(), name="community-create"),
    path("<str:name>/", views.CommunityDetailView.as_view(), name="community-detail"),
    path("<str:name>/join/", views.CommunityJoinView.as_view(), name="community-join"),
    path(
        "<str:name>/leave/", views.CommunityLeaveView.as_view(), name="community-leave"
    ),
    path("<str:name>/post/", include("posts.urls")),
]
