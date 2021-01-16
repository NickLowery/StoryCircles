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

class CircleManager(models.Manager):
    def create_circle(self, title):
        circle = self.create(story=Story.objects.create(title=title))
        circle.save()
        return circle

class Story(models.Model):
    title = models.TextField(unique=True)
    authors = models.ManyToManyField(
        User,
        related_name="works",
        blank=True
    )
    text = models.TextField()
    finished = models.BooleanField(default=False)

class Circle(models.Model):
    # This is a list of the usernames of users in the turn order. First name
    # is the user whose turn it is.
    turn_order = models.JSONField(default=list)
    approved_ending = models.ManyToManyField(
        User,
        blank=True
    )
    story = models.OneToOneField(
        'Story',
        blank=True,
        on_delete=models.CASCADE,
    )
    objects = CircleManager()

    # This will be used as the channel layer group name.
    @property
    def group_name(self):
        return 'circle_' + self.story.title.replace(" ", "_")

    # End the story and return a reference to the finished story instance.
    def finish_story(self):
        story = self.story
        story.finished = True
        story.save()
        self.delete()
        return story

    # Check if everyone in the game has approved ending the story in its current state
    def all_approve_ending(self):
        approved_usernames = list(user.username for user in self.approved_ending.all())
        return all((username in approved_usernames) for username in self.turn_order)

    #TODO: I need to figure out something to do with orphaned story instances that don't get finished, probably

