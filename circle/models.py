from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import F
from django.utils.translation import gettext_lazy as _
import datetime

class User(AbstractUser):
    user_since = models.DateTimeField(blank=False, auto_now_add=True)
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

# Stories in progress allowing more users (i.e. excludes waiting circles)
class OpenCircleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(user_ct__lt=F('max_user_ct'), story__start_time__isnull=False)

class WaitingCircleManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(story__start_time__isnull=True)

class Story(models.Model):
    title = models.TextField(unique=True)
    authors = models.ManyToManyField(
        User,
        related_name="stories",
        blank=True
    )
    text = models.TextField()
    start_time = models.DateTimeField(blank=True, null=True)
    finish_time = models.DateTimeField(blank=True, null=True)
    finished = models.BooleanField(default=False)

    @property
    def started(self):
        return (self.start_time is not None)

    def get_absolute_url(self):
        if self.finished:
            return reverse('finished_story', args = [self.pk])
        else:
            # TODO: Use this in list of working stories
            return reverse('circle', args = [self.circle.pk])

    def append_text(self, new_text):
        # NOTE: Throw an error if we try to append when story is finished or not started?
        self.text += new_text
        self.save()

    def start(self):
        self.start_time = datetime.datetime.now()
        self.save()

class Circle(models.Model):
    # This is a list of the usernames of users in the turn order. First name
    # is the user whose turn it is.
    creation_time = models.DateTimeField(auto_now_add=True)

    threshold_user_ct = models.IntegerField() #This is the number of users that must be connected to start the story
    max_user_ct = models.IntegerField()
    user_ct = models.IntegerField(default=0)
    turn_order = models.JSONField(default=list)

    class Proposal(models.TextChoices):
        END_STORY = 'ES', _('End Story')
        NEW_PARAGRAPH = 'NP', _('New Paragraph')

        def gerund(self):
            if self.name == 'END_STORY':
                return 'ending the story'
            elif self.name == 'NEW_PARAGRAPH':
                return 'starting a new paragraph'

    active_proposal = models.CharField(
        max_length=2,
        choices=Proposal.choices,
        blank=True,
        null=True,
    )
    proposing_user = models.ForeignKey('User',
                                        null=True, on_delete=models.SET_NULL,
                                        related_name='ending_proposed')
    approved_proposal = models.ManyToManyField(
        User,
        blank=True
    )

    story = models.OneToOneField(
        'Story',
        blank=True,
        on_delete=models.CASCADE,
    )

    objects = CircleManager()
    open_circles = OpenCircleManager()
    waiting_circles = WaitingCircleManager()

    #The number of users needed to meet the start threshold
    @property
    def users_needed(self):
        return max(0, self.threshold_user_ct - self.user_ct)

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
    def all_approve_proposal(self):
        approved_usernames = list(user.username for user in self.approved_proposal.all())
        return all((username in approved_usernames) for username in self.turn_order)

    # Get rid of active proposal, reset proposal state, and save
    def reset_proposal(self):
        self.approved_proposal.clear()
        self.proposing_user = None
        self.active_proposal = None
        self.save()

    #TODO: I need to figure out something to do with orphaned story instances that don't get finished, probably

