import json
import re
import string
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .models import WorkingStory, User

class CircleConsumer(WebsocketConsumer):
    # When a client connects
    def connect(self):
        self.circle_name = self.scope['url_route']['kwargs']['circle_name']
        self.circle_group_name = 'circle_%s' % self.circle_name
        # TODO: Make sure group names are valid?

        self.user_instance = User.objects.get(username=self.scope['user'])
        # TODO: Do I actually need the user instance for anything or do I
        # just need the username?

        # Get the model and send text
        story_instance, created = WorkingStory.objects.get_or_create(
            circle_name=self.circle_name)

        # Update turn_order
        turn_order = json.loads(story_instance.turn_order_json)
        if (self.user_instance.username not in turn_order):
            turn_order.append(self.user_instance.username)
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
        story_instance = WorkingStory.objects.get(circle_name=self.circle_name)
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
        story_instance = WorkingStory.objects.get(circle_name=self.circle_name)
        text_data_json = json.loads(text_data)
        message_process_func = {
            "word_submit": self.word_submit,
            "propose_end": self.propose_end,
            "approve_end": self.approve_end,
            "reject_end": self.reject_end,
        }.get(text_data_json['type'])
        message_process_func(text_data_json, story_instance)


    # Process proposal to end the story from client
    def propose_end(self, text_data_json, story_instance):
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
    def approve_end(self, text_data_json, story_instance):
        if (self.user_instance in story_instance.approved_ending.all()):
            self.msg_clinet("You have already approved the ending")
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

    def reject_end(self, text_data_json, story_instance):
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
    def word_submit(self, text_data_json, story_instance):
        word = text_data_json['word']
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
        # Send message to WebSocket
        # self.update_client(event['text'], event['turn_order'])

    # Update client with new state of the game
    # def update_client(self, text, turn_order):
        # self.send(text_data=json.dumps({
        #     'type': 'game_update',
        #     'text': text,
        #     'turn_order': turn_order
        # }))

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
        if text[-1].isalpha():
            return (True, word, "")
        else:
            return (False, "", "You can only hyphenate after a word.")
    else:
        return (False, "", "Not a valid word for some reason (disallowed characters?)")
