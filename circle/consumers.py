import json
import re
import string
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .models import WorkingStory, User, FinishedStory
from .views import FinishedStoryView, CircleView
from django.urls import reverse
from django.shortcuts import get_object_or_404

class CircleIndexConsumer(WebsocketConsumer):
    def connect(self):
        self.user_instance = User.objects.get(username=self.scope['user'])
        self.accept()
        self.send(text_data=json.dumps(
            {
                'type':'message',
                'message_text':"Index connection accepted"
            }))

    def receive(self, text_data):
        data = json.loads(text_data)
        if data['type'] == 'circle_create':
            title = data['title']
            self.send(text_data=json.dumps(
                {
                    'type':'message',
                    'message_text':'Request to start story "%s" received' % title
                }))
            # Validate title
            # It should contain at least one letter, and nothing but letters, digits, and spaces
            if validate_title(title):
                new_story = WorkingStory(title=title)
                new_story.save()
                self.send(text_data=json.dumps(
                    {
                        'type':'redirect',
                        'message_text':'Story "%s" created' % title,
                        'url': reverse("circle", kwargs={'pk': new_story.pk})
                    }))
            else:
                self.send(text_data=json.dumps(
                    {
                        'type':'message',
                        'message_text':'Invalid title'
                    }))


    def disconnect(self, close_code):
        pass

class CircleConsumer(WebsocketConsumer):
    # When a client connects
    def connect(self):
        # This will fail if the user isn't logged in, so maybe I'm good as far as authentication?
        self.user_instance = User.objects.get(username=self.scope['user'])

        self.story_pk = int(self.scope['url_route']['kwargs']['story_pk_string'])
        story_instance = get_object_or_404(WorkingStory, pk=self.story_pk)
        self.circle_group_name = 'circle_%s' % story_instance.title
        # TODO: Make sure group names are valid?

        # Update turn_order
        if story_instance.turn_order_json:
            turn_order = json.loads(story_instance.turn_order_json)
            if (self.user_instance.username not in turn_order):
                turn_order.append(self.user_instance.username)
        else:
            turn_order = [self.user_instance.username]

        story_instance.turn_order_json = json.dumps(turn_order)

        # Update final authors list
        story_instance.authors.add(self.user_instance)
        story_instance.save()

        # Join circle group
        async_to_sync(self.channel_layer.group_add)(
            self.circle_group_name,
            self.channel_name
        )

        # Check if there is a pending ending
        approved_ending_list = [author.username for author in story_instance.approved_ending.all()]

        # Send message to the circle
        async_to_sync(self.channel_layer.group_send)(
            self.circle_group_name,
            {
                'type': 'update',
                'text': story_instance.text,
                'turn_order': turn_order,
                'approved_ending_list': approved_ending_list,
            }
        )
        self.accept()

    # Runs when a client disconnects
    def disconnect(self, close_code):
        # Update turn schedule
        story_instance = WorkingStory.objects.get(pk=self.story_pk)
        turn_order = json.loads(story_instance.turn_order_json)
        while (self.user_instance.username in turn_order):
            turn_order.remove(self.user_instance.username)
        # NOTE: Only one remove should be necessary if this is working right
        story_instance.turn_order_json = json.dumps(turn_order)
        story_instance.save()

        # Leave circle group
        async_to_sync(self.channel_layer.group_discard)(
            self.circle_group_name,
            self.channel_name
        )
        # TODO: Eventually we need some kind of timeout


    # Receive message from WebSocket
    def receive(self, text_data):
        story_instance = WorkingStory.objects.get(pk=self.story_pk)
        data = json.loads(text_data)
        message_process_func = {
            "word_submit": self.word_submit,
            "propose_end": self.propose_end,
            "approve_end": self.approve_end,
            "reject_end": self.reject_end,
        }.get(data['type'])
        message_process_func(data, story_instance)


    # Process proposal to end the story from client
    def propose_end(self, data, story_instance):
        self.msg_client("Proposal to end the story received.")
        #NOTE: This should only be an option if there isn't already a 
        # proposal to end the story
        if story_instance.approved_ending.all():
                self.msg_client("Error: There is already a pending proposal to end the story")
        else:
            story_instance.approved_ending.add(self.user_instance)
            story_instance.save()
            approved_ending_list = [user.username for user in story_instance.approved_ending.all()]
            turn_order = json.loads(story_instance.turn_order_json)
            async_to_sync(self.channel_layer.group_send)(
                self.circle_group_name,
                {
                    'type': 'update',
                    'text': story_instance.text,
                    'turn_order': turn_order,
                    'approved_ending_list': approved_ending_list,
                }
            )

    # Process ending approval from client
    def approve_end(self, data, story_instance):
        if (self.user_instance in story_instance.approved_ending.all()):
            self.msg_clinet("You have already approved the ending")
        else:
            story_instance.approved_ending.add(self.user_instance)
            story_instance.save()
            approved_ending_list = [user.username for user in story_instance.approved_ending.all()]
            turn_order = json.loads(story_instance.turn_order_json)
            # If everyone in the turn order has approved the ending, the story should end here.
            if all((username in approved_ending_list) for username in turn_order):
                finished_story = FinishedStory(text=story_instance.text)
                finished_story.save()
                finished_story.authors.set(story_instance.authors.all())
                story_instance.delete()
                async_to_sync(self.channel_layer.group_send)(
                    self.circle_group_name,
                    {
                        'type': 'story_finished',
                        'redirect': reverse(FinishedStoryView(pk=finished_story.pk))
                    }
                )

            async_to_sync(self.channel_layer.group_send)(
                self.circle_group_name,
                {
                    'type': 'update',
                    'text': story_instance.text,
                    'turn_order': turn_order,
                    'approved_ending_list': approved_ending_list,
                }
            )

    def reject_end(self, data, story_instance):
        story_instance.approved_ending.clear()
        story_instance.save()
        approved_ending_list = []
        turn_order = json.loads(story_instance.turn_order_json)
        async_to_sync(self.channel_layer.group_send)(
            self.circle_group_name,
            {
                'type': 'update',
                'text': story_instance.text,
                'turn_order': turn_order,
                'approved_ending_list': approved_ending_list,
                'message': "%s rejected ending the story at this point."
                % self.user_instance.username
            }
        )


    # Process word submission from client
    def word_submit(self, data, story_instance):
        word = data['word']
        turn_order = json.loads(story_instance.turn_order_json)
        #It has to be our client's turn
        if (turn_order[0] != self.user_instance.username):
            self.msg_client('Error: we got a word submission from ' \
                                'your browser when it was not your turn.')
        # No submitting words when there's an ending of the story proposed
        elif story_instance.approved_ending.all():
            self.msg_client("Error: Can't submit a word when an ending " \
                                "of the story is pending.")

        else:
            valid, formatted_word, message = validate_word(word, story_instance.text)

            if (valid):
                # Update text
                story_instance.text += formatted_word

                # Update whose turn it is
                turn_order = json.loads(story_instance.turn_order_json)
                turn_order.append(turn_order.pop(0))
                story_instance.turn_order_json = json.dumps(turn_order)

                # Update database
                story_instance.save()

                # Send message to the circle
                async_to_sync(self.channel_layer.group_send)(
                    self.circle_group_name,
                    {
                        'type': 'update',
                        'text': story_instance.text,
                        'turn_order': turn_order,
                        'approved_ending_list': [],
                    }
                )
            else:
                self.msg_client(message)

    # Receive game update message from circle
    def update(self, event):
        data = {
            'type': 'game_update',
            'text': event['text'],
            'turn_order': event['turn_order'],
            'approved_ending_list': event['approved_ending_list'],
        }
        message =  event.get('message')
        if message:
            data['message'] = message
        self.send(text_data=json.dumps(data))

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
            return (True, word, "")
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
