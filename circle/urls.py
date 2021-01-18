from django.urls import path

from . import views

urlpatterns = [
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register_view, name="register"),
    path('', views.index, name='index'),
    path('stories', views.FinishedStoryListView.as_view(), name='finished_stories'),
    path("circle/<int:pk>", views.CircleView.as_view(), name="circle"),
    path("user/<int:pk>", views.UserDetailView.as_view(), name="user"),
    path("story/<int:pk>", views.FinishedStoryView.as_view(), name="finished_story"),
]
