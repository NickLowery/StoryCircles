from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    liked_stories = models.ManyToManyField(
        "Story",
        related_name="liked_by",
        blank=True,
    )

    # Can use this later if we want user profiles pages
    # def get_absolute_url(self):
    #     return reverse('user_profile', args=[self.username])

class Circle(models.Model):
    # This is a list of the usernames of users in the turn order. First name
    # is the user whose turn it is.
    turn_order = models.JSONField(default=list)
    approved_ending = models.ManyToManyField(
        User,
        blank=True
    )
    @property
    def group_name(self):
        self.story.title.replace(" ", "_")

class Story(models.Model):
    title = models.TextField(unique=True)
    authors = models.ManyToManyField(
        User,
        related_name="works",
        blank=True
    )
    text = models.TextField()
    finished = models.BooleanField(default=False)
    circle = models.OneToOneField(
        Circle,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )


