import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .models import User, Story, Circle
from .views import FinishedStoryView, CircleView
from .rules import validate_word, validate_title
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.template.loader import get_template

class WriteIndexConsumer(WebsocketConsumer):
    """Handle submission of new story on Write page"""
    def connect(self):
        self.user_instance = User.objects.get(username=self.scope['user'])
        self.accept()

    def receive(self, text_data):
        data = json.loads(text_data)
        if data['type'] == 'circle_create':
            title = data['title']
            threshold_user_ct = data['threshold_user_ct']
            max_user_ct = data['max_user_ct']
            self.msg_client('Request to start story "%s" received' % title)
            # Validate title
            # It should contain at least one letter, and nothing but letters, digits, and spaces
            if not validate_title(title):
                self.msg_client('Invalid title')
            elif threshold_user_ct > max_user_ct:
                self.msg_client('Minimum users cannot be greater than maximum users')
            else:
                circle = Circle.objects.create_circle(title,
                                                      threshold_user_ct=threshold_user_ct,
                                                      max_user_ct=max_user_ct)
                self.send(text_data=json.dumps(
                    {
                        'type':'redirect',
                        'message_text':'Story "%s" created' % title,
                        'url': reverse("circle", kwargs={'pk': circle.pk})
                    }))

    def disconnect(self, close_code):
        pass

    def msg_client(self, message):
        self.send(text_data=json.dumps({
            'type': 'message',
            'message_text': message,
        }))

class CircleConsumer(WebsocketConsumer):
    """Handles Websocket connection between user and Circle"""
    def connect(self):
        """Handle client connecting to Circle. Only logged in Users will be 
        accepted. Start the story if necessary. Update the group"""
        self.user_instance = User.objects.get(username=self.scope['user'])

        self.circle_pk = int(self.scope['url_route']['kwargs']['circle_pk_string'])
        circle_instance = get_object_or_404(Circle, pk=self.circle_pk, story__finished=False)

        if circle_instance.user_ct >= circle_instance.max_user_ct:
            self.accept()
            self.redirect_client(reverse("index"),
                     "Error: There are too many users in this circle already. \
                     You will be redirected back to the Write page in 5 seconds.")
            self.close()

        # Put our user at the end of the turn order
        if (self.user_instance.username not in circle_instance.turn_order):
            circle_instance.turn_order.append(self.user_instance.username)
        circle_instance.user_ct = len(circle_instance.turn_order)

        # Start story if needed.
        if (circle_instance.user_ct >= circle_instance.threshold_user_ct
                and not circle_instance.story.started):
            circle_instance.story.start()

        # Update final authors list
        circle_instance.story.authors.add(self.user_instance)

        # Remember group name (we need it here for disconnect)
        self.group_name = circle_instance.group_name

        circle_instance.save()

        # Join circle group
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

        # Send message to the circle
        self.update_group(circle_instance)
        self.accept()

    def disconnect(self, close_code):
        """Update the Circle when a user disconnects"""
        # Update turn schedule if Circle still exists
        try:
            circle_instance = Circle.objects.get(pk=self.circle_pk)
            circle_instance.turn_order.remove(self.user_instance.username)
            circle_instance.user_ct = len(circle_instance.turn_order)
            self.update_group(circle_instance)
            circle_instance.save()
        except Circle.DoesNotExist:
            # Nothing to do because circle is already deleted
            pass

        # Leave circle group
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    # --METHODS RECEIVING MESSAGES FROM CLIENT--
    def receive(self, text_data):
        """Dispatch messages from client to approporiate methods"""
        circle_instance = Circle.objects.get(pk=self.circle_pk)
        data = json.loads(text_data)
        method_for_message_type = {
            "word_submit": self.word_submit,
            "propose": self.propose,
            "approve": self.approve,
            "reject": self.reject,
        }.get(data['type'])
        method_for_message_type(data, circle_instance)

    def propose(self, data, circle_instance):
        """Process proposal from User that requires unanimous consent"""
        if data['proposal'] not in Circle.Proposal.values:
            self.msg_client("Error: Unknown proposal.")
        elif circle_instance.active_proposal:
            self.msg_client("Error: There is already a pending proposal.")
        elif circle_instance.turn_order[0] != self.user_instance.username:
            self.msg_client("Error: You can only make a proposal if it's your turn")
        else:
            circle_instance.active_proposal = data['proposal']
            circle_instance.proposing_user = self.user_instance
            circle_instance.approved_proposal.add(self.user_instance)
            self.check_approval_and_update(circle_instance)

    def approve(self, data, circle_instance):
        """Process User approving proposal"""
        if (circle_instance.active_proposal != data['proposal']):
            self.msg_client("Error: The proposal you approved is not active.")
        elif (self.user_instance in circle_instance.approved_proposal.all()):
            self.msg_client("You have already approved the proposal.")
        else:
            circle_instance.approved_proposal.add(self.user_instance)
            self.check_approval_and_update(circle_instance)

    def check_approval_and_update(self, circle_instance):
        """ See if a proposal has been unanimously approved, take appropriate action
        if it has, save the circle instance and update the group """
        if circle_instance.all_approve_proposal():
            if circle_instance.active_proposal == Circle.Proposal.END_STORY:
                self.end_story(circle_instance)
            elif circle_instance.active_proposal == Circle.Proposal.NEW_PARAGRAPH:
                self.msg_client("New paragraph initiated")
                circle_instance.story.append_paragraph_break()
                circle_instance.reset_proposal()
                self.update_group(circle_instance)
        else:
            circle_instance.save()
            self.update_group(circle_instance)


    def reject(self, data, circle_instance):
        """Process user rejecting proposal"""
        proposal = Circle.Proposal(circle_instance.active_proposal)
        circle_instance.reset_proposal()
        self.update_group(circle_instance,
                          message=f"{self.user_instance.username} rejected {proposal.gerund()}."
                          )

    def word_submit(self, data, circle_instance):
        """Process word submission from User"""
        #It has to be our client's turn
        if (circle_instance.turn_order[0] != self.user_instance.username):
            self.msg_client('Error: we got a word submission from ' \
                                'your browser when it was not your turn.')
        # No submitting words when there's an active proposal
        elif circle_instance.active_proposal:
            self.msg_client("Error: Can't submit a word when a proposal is pending.")
        else:
            valid, formatted_word, message = validate_word(data['word'], circle_instance.story.text)

            if (valid):
                # Update text
                circle_instance.story.append_text(formatted_word)

                # Update whose turn it is
                circle_instance.turn_order.append(circle_instance.turn_order.pop(0))

                # Update database
                circle_instance.save()

                # Send message to the circle
                self.update_group(circle_instance)
            else:
                self.msg_client(message)

    # --METHODS RECEIVING MESSAGES FROM THE CIRCLE
    def story_finished(self, event):
        """Receive story finished message from the Circle"""
        self.redirect_client(event['redirect'],
                             "Story finished! You will be redirected to its permanent home in a few seconds.")

    def game_update(self, event):
        """Receive game update message from Circle"""
        self.send(text_data=json.dumps(event))

    # --METHODS SENDING MESSAGES TO THE CIRCLE 
    def update_group(self, circle_instance, message=None):
        """Send a game state update to the Circle"""
        data = {'type': 'game_update',
                'story_started': circle_instance.story.started,
                'text_html': circle_instance.story.text_as_html(),
                'turn_order': circle_instance.turn_order,
            }
        if circle_instance.active_proposal:
            data.update({
                'proposing_user': circle_instance.proposing_user.username,
            'active_proposal':  circle_instance.active_proposal,
            'approved_proposal_list': [author.username for author
                                     in circle_instance.approved_proposal.all()],
            })
        if message:
            data['message'] = message
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            data
        )

    def end_story(self, circle_instance):
        """End story and send a message to the circle"""
        finished_story = circle_instance.finish_story()
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'story_finished',
                'redirect': finished_story.get_absolute_url()
            }
        )

    # --BASIC METHODS SENDING MESSAGES TO CLIENT
    def msg_client(self, message):
        """Send a message to client"""
        self.send(text_data=json.dumps({
            'type': 'message',
            'message_text': message,
        }))

    def redirect_client(self, redirect_url, message):
        """Redirect client to a different page"""
        self.send(text_data=json.dumps({
            'type': 'redirect',
            'redirect_url': redirect_url,
            'message_text': message,
        }))
