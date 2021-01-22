import json
import re
import string
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .models import User, Story, Circle
from .views import FinishedStoryView, CircleView
from django.urls import reverse
from django.shortcuts import get_object_or_404

class CircleIndexConsumer(WebsocketConsumer):
    def connect(self):
        self.user_instance = User.objects.get(username=self.scope['user'])
        self.accept()
        self.msg_client("Index connection accepted")

    def receive(self, text_data):
        data = json.loads(text_data)
        if data['type'] == 'circle_create':
            title = data['title']
            threshold_user_ct = data['threshold_user_ct']
            max_user_ct = data['max_user_ct']
            self.msg_client('Request to start story "%s" received' % title)
            # Validate title
            # It should contain at least one letter, and nothing but letters, digits, and spaces
            if validate_title(title):
                # NOTE: It might be good to encapsulate this in creating the new story
                # TODO: Right now we crash if the story title is not unique, handle that.
                circle = Circle.objects.create_circle(title,
                                                      threshold_user_ct=threshold_user_ct,
                                                      max_user_ct=max_user_ct)
                self.send(text_data=json.dumps(
                    {
                        'type':'redirect',
                        'message_text':'Story "%s" created' % title,
                        'url': reverse("circle", kwargs={'pk': circle.pk})
                    }))
            else:
                self.msg_client('Invalid title')

    def disconnect(self, close_code):
        pass

    def msg_client(self, message):
        self.send(text_data=json.dumps({
            'type': 'message',
            'message_text': message,
        }))

class CircleConsumer(WebsocketConsumer):
    # When a client connects
    def connect(self):
        # This will fail if the user isn't logged in, so maybe I'm good as far as authentication?
        self.user_instance = User.objects.get(username=self.scope['user'])
        # TODO: Only accept connection if there is room for another author.

        self.circle_pk = int(self.scope['url_route']['kwargs']['circle_pk_string'])
        #TODO: Redirect the user if the story is finished.
        circle_instance = get_object_or_404(Circle, pk=self.circle_pk, story__finished=False)

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

    # Runs when a client disconnects
    def disconnect(self, close_code):
        # Update turn schedule
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
        # TODO: Eventually we need some kind of timeout for removing users or at least
        # skipping them in the order

    # --METHODS RECEIVING MESSAGES FROM CLIENT--
    # Receive message from WebSocket
    def receive(self, text_data):
        circle_instance = Circle.objects.get(pk=self.circle_pk)
        data = json.loads(text_data)
        method_for_message_type = {
            "word_submit": self.word_submit,
            "propose_end": self.propose_end,
            "approve_end": self.approve_end,
            "reject_end": self.reject_end,
        }.get(data['type'])
        method_for_message_type(data, circle_instance)

    # Process proposal to end the story from client
    def propose_end(self, data, circle_instance):
        if circle_instance.approved_ending.all():
            self.msg_client("Error: There is already a pending proposal to end the story")
        elif circle_instance.turn_order[0] != self.user_instance.username:
            self.msg_client("Error: You can only propose ending the story if it's your turn")
        else:
            self.msg_client("Proposal to end the story received.")
            circle_instance.approved_ending.add(self.user_instance)
            if circle_instance.all_approve_ending():
                self.end_story(circle_instance)
            else:
                circle_instance.save()
                self.update_group(circle_instance)

    # Process ending approval from client
    def approve_end(self, data, circle_instance):
        if (self.user_instance in circle_instance.approved_ending.all()):
            self.msg_client("You have already approved the ending")
        else:
            circle_instance.approved_ending.add(self.user_instance)
            if circle_instance.all_approve_ending():
                self.end_story(circle_instance)
            else:
                circle_instance.save()
                self.update_group(circle_instance)

    # Process ending rejection from client
    def reject_end(self, data, circle_instance):
        circle_instance.approved_ending.clear()
        circle_instance.save()
        self.update_group(circle_instance,
                          message="%s rejected ending the story at this point."
                % self.user_instance.username)

    # Process word submission from client
    def word_submit(self, data, circle_instance):
        #It has to be our client's turn
        if (circle_instance.turn_order[0] != self.user_instance.username):
            self.msg_client('Error: we got a word submission from ' \
                                'your browser when it was not your turn.')
        # No submitting words when there's an ending of the circle proposed
        elif circle_instance.approved_ending.all():
            self.msg_client("Error: Can't submit a word when an ending " \
                                "of the circle is pending.")

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

    # --METHODS SENDING AND RECEIVING FROM CIRCLE
    # Receive story finished message from the circle
    def story_finished(self, event):
        self.send(text_data=json.dumps({
            'type': 'story_finished',
            'redirect_url': event['redirect']
        }))

    # Receive game update message from circle
    def update(self, event):
        data = {
            'type': 'game_update',
            'story_started': event['started'],
            'text': event['text'],
            'turn_order': event['turn_order'],
            'approved_ending_list': event['approved_ending_list'],
        }
        message =  event.get('message')
        if message:
            data['message'] = message
        self.send(text_data=json.dumps(data))

    # Send a game state update to the circle
    def update_group(self, circle_instance, message=None):
        data = {'type': 'update',
                'started': circle_instance.story.started,
                'text': circle_instance.story.text,
                'turn_order': circle_instance.turn_order,
                'approved_ending_list': [author.username for author
                                         in circle_instance.approved_ending.all()],
            }
        if message:
            data['message'] = message
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            data
        )

    # End story and send a message to the circle
    def end_story(self, circle_instance):
        finished_story = circle_instance.finish_story()
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                'type': 'story_finished',
                'redirect': finished_story.get_absolute_url()
            }
        )

    # --OTHER COMMUNICATION METHODS
    # Send a message to client
    def msg_client(self, message):
        self.send(text_data=json.dumps({
            'type': 'message',
            'message_text': message,
        }))

# Check if something is a valid "word" submission with previous existing text.
# Return (valid, formatted_word, message), where valid is a boolean, formatted_word is
# the word ready to be added to existing text (adding a space if applicable), and 
# message is an error message if the word was not valid.
# It can be a word, or ?, !, . for now. Can make it a little more complicated later.
# TODO: Move this into some appropriate other file since it's not a consumer?
def validate_word(word, text):
    if not text:
        if re.fullmatch("[a-zA-Z']+", word):
            return (True, string.capwords(word), "")
        else:
            return (False, "", "Story must begin with a word")
    if " " in word:
        return (False, "", "Word cannot contain spaces.")
    if word in ["?", ".", "!"]:
        if text[-1].isalpha():
            return (True, word, "")
        else:
            return (False, "", "Sentence-ending punctuation can only go after a word.")
    if re.fullmatch("[a-zA-Z']+", word):
        if text[-1] in ["?", ".", "!"]:
            return (True, (' ' + string.capwords(word)), "")
        else:
            return (True, (' ' + word), "")
    if re.fullmatch("\-[a-zA-Z']+", word):
        if not text[-1].isalpha():
            return (False, "", "You can only hyphenate after a word.")
        elif re.search("'", word):
            return (False, "", "I can't think of a case where an apostrophe after a hyphen would be valid.")
        else:
            return (True, word, "")
    else:
        return (False, "", "Not a valid word for some reason (disallowed characters?)")

# Check if a story title is valid. It needs to contain at least one letter and nothing but 
# letters, digits, and spaces. Return True if valid, False if not
# TODO: Would it be worth it to allow apostrophes?
def validate_title(title):
    if re.search("[a-zA-Z]", title) and re.fullmatch("[a-zA-Z0-9\ ]+", title):
        return True
    else:
        return False
