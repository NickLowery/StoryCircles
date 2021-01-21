from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
import datetime

class User(AbstractUser):
    liked_stories = models.ManyToManyField(
        "Story",
        related_name="liked_by",
        blank=True,
    )

    def get_absolute_url(self):
        return reverse('user', args=[self.pk])

class CircleManager(models.Manager):
    def create_circle(self, title, **kwargs):
        circle = self.create(story=Story.objects.create(title=title), **kwargs)
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
    # TODO: This needs to be set when threshold user ct is reached
    start_time = models.DateTimeField(blank=True, null=True)
    finish_time = models.DateTimeField(blank=True, null=True)
    finished = models.BooleanField(default=False)

    def get_absolute_url(self):
        if self.finished:
            return reverse('finished_story', args = [self.pk])
        else:
            # TODO: Use this in list of working stories
            return reverse('circle', args = [self.circle.pk])

    def append_text(self, new_text):
        self.text += new_text
        self.save()

class Circle(models.Model):
    # This is a list of the usernames of users in the turn order. First name
    # is the user whose turn it is.
    creation_time = models.DateTimeField(auto_now_add=True)

    threshold_user_ct = models.IntegerField( #This is the number of users that must be connected to start the story
        validators=[MinValueValidator(2),
                    MaxValueValidator(100)]
    )
    max_user_ct = models.IntegerField(
        validators=[MinValueValidator(2),
                    MaxValueValidator(100)]
    )
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
        story.finish_time = datetime.datetime.now()
        story.save()
        self.delete()
        return story

    # Check if everyone in the game has approved ending the story in its current state
    def all_approve_ending(self):
        approved_usernames = list(user.username for user in self.approved_ending.all())
        return all((username in approved_usernames) for username in self.turn_order)

    #TODO: I need to figure out something to do with orphaned story instances that don't get finished, probably

