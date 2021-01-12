from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path("circle/<int:pk>", views.CircleView.as_view(), name="circle"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register_view, name="register"),
    path("story/<int:pk>", views.FinishedStoryView.as_view(), name="story"),
]
