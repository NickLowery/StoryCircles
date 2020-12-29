from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    liked_stories = models.ManyToManyField(
        "FinishedStory",
        related_name="liked_by",
        blank=True,
    )

    # Can use this later if we want user profiles pages
    # def get_absolute_url(self):
    #     return reverse('user_profile', args=[self.username])

class FinishedStory(models.Model):
    authors = models.ManyToManyField(
        User,
        related_name="works"
    )
    text = models.TextField()

class WorkingStory(models.Model):
    circle_name = models.TextField()
    authors = models.ManyToManyField(
        User,
        related_name="wip",
        blank=True
    )
    text = models.TextField()
    turn_order_json = models.TextField() # in turn order, whoever is "it" is
        # first

