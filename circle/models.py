from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import F
from django.utils.translation import gettext_lazy as _
from django.template.loader import get_template
import datetime
import re

class User(AbstractUser):
    """A registered user"""
    user_since = models.DateTimeField(blank=False, auto_now_add=True)

    def get_absolute_url(self):
        return reverse('user', args=[self.pk])

class Story(models.Model):
    """Represents a story, which could be in progress or finished"""
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
        """The story being "started" is represented by start_time being non-null"""
        return (self.start_time is not None)

    def get_absolute_url(self):
        if self.finished:
            return reverse('finished_story', args = [self.pk])
        else:
            return reverse('circle', args = [self.circle.pk])

    def append_text(self, new_text):
        self.text += new_text
        self.save()

    def start(self):
        self.start_time = datetime.datetime.now()
        self.save()

    def text_as_html(self):
        """ Return the text as html with "\n\n" converted to paragraph breaks """
        t = get_template('circle/story_text.html')
        text = t.render({'story': self}).rstrip()
        return text

class CircleManager(models.Manager):
    """Manager to provide a standard method of creating a Circle with its associated Story"""

    def create_circle(self, title, **kwargs):
        circle = self.create(story=Story.objects.create(title=title), **kwargs)
        circle.save()
        return circle

class OpenCircleManager(models.Manager):
    """Stories in progress allowing more users (i.e. excludes waiting circles)"""

    def get_queryset(self):
        return super().get_queryset().filter(user_ct__lt=F('max_user_ct'), story__start_time__isnull=False)

class WaitingCircleManager(models.Manager):
    """Stories waiting for more users to start"""

    def get_queryset(self):
        return super().get_queryset().filter(story__start_time__isnull=True)

class Circle(models.Model):
    """ Represents the (possibly-empty) group of users working on an in-progress Story"""
    creation_time = models.DateTimeField(auto_now_add=True)

    threshold_user_ct = models.IntegerField() # The number of users that must be connected to start the story
    max_user_ct = models.IntegerField()
    user_ct = models.IntegerField(default=0)
    turn_order = models.JSONField(default=list) # Represented with a list of
    # usernames starting with the user whose turn it is

    class Proposal(models.TextChoices):
        """Choices of possible actions that can be proposed and need unanimous
        consent from active authors"""
        END_STORY = 'ES', _('End Story')
        NEW_PARAGRAPH = 'NP', _('New Paragraph')

        def gerund(self):
            """Text description of the represented action"""
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
    ) # Users who have approved the active proposal
    story = models.OneToOneField(
        'Story',
        blank=True,
        on_delete=models.CASCADE,
    )
    objects = CircleManager()
    open_circles = OpenCircleManager()
    waiting_circles = WaitingCircleManager()

    @property
    def users_needed(self):
        """The number of users remaining to meet the start threshold"""
        return max(0, self.threshold_user_ct - self.user_ct)

    @property
    def group_name(self):
        """To be used as the channel layer group name"""
        return 'circle_' + self.story.title.replace(" ", "_")

    def finish_story(self):
        """End the story and return a reference to the finished Story."""
        story = self.story
        story.finished = True
        story.finish_time = datetime.datetime.now()
        story.save()
        self.delete()
        return story

    def all_approve_proposal(self):
        """Check if everyone in the game has approved the current proposal and
        return as a Boolean"""
        approved_usernames = list(user.username for user in self.approved_proposal.all())
        return all((username in approved_usernames) for username in self.turn_order)

    def reset_proposal(self):
        """Get rid of active proposal, reset proposal state, and save"""
        self.approved_proposal.clear()
        self.proposing_user = None
        self.active_proposal = None
        self.save()
