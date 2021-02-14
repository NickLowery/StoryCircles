import itertools
from django.test import TestCase
from .consumers import validate_word, validate_title
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from storycircles.asgi import application as asgi_app
from asgiref.sync import async_to_sync, sync_to_async
from circle.models import User

# Create your tests here.

class ValidateWordTestCase(TestCase):
    #TODO: Test for first word

    def test_title_case(self):
        """After sentence-ending punctuation or newline, the next word should be
        capitalized."""
        self.assertEqual((True, " I"), validate_word("i", "ending.")[:-1])
        self.assertEqual((True, " Island"), validate_word("island", "ending.")[:-1])
        self.assertEqual((True, " I'm"), validate_word("i'm", "ending.")[:-1])
        self.assertEqual((True, " I"), validate_word("i", "ending.\n")[:-1])
        self.assertEqual((True, " Island"), validate_word("island", "ending.\n")[:-1])
        self.assertEqual((True, " I'm"), validate_word("i'm", "ending.\n")[:-1])

    def test_sentence_ending(self):
        """Sentence-ending should work only by itself and after a word"""
        for punct in [".", "!", "?"]:
            self.assertEqual((True, punct), validate_word(punct, "word")[:-1])
            self.assertEqual((True, punct), validate_word(punct, "isn't")[:-1])
            self.assertEqual((True, punct), validate_word(punct, "lily-livered")[:-1])
            self.assertFalse(validate_word(punct, "ending.\n")[0])
        for (p1,p2) in itertools.product([".", "!", "?"], repeat=2):
            self.assertFalse(validate_word(p1, ("ending" + p2))[0])
        for (word, text) in itertools.product(['word.', 'word?', 'word!'],['word', 'ending.',
                                                                     "isn't", "lily-livered"]):
            self.assertFalse(validate_word(word, text)[0])

    def test_space(self):
        """Any submission with a space in it should fail"""
        for (word, text) in itertools.product([' ', ' word', 'a b'],['word', 'ending.',
                                                                     "isn't", "lily-livered"]):
            self.assertFalse(validate_word(word, text)[0])

    def test_hyphenation(self):
        """ Hyphenation should work by adding a hyphen and a word, only after a word """
        text = 'anxiety'
        hyphen_word = '-ridden'
        self.assertEqual((True, hyphen_word), validate_word(hyphen_word, text)[:-1])

        # A hyphen by itself or followed by punctuation should always fail
        for text in ('word', 'ending.', "isn't"):
            self.assertFalse(validate_word("-", text)[0])
            self.assertFalse(validate_word("-.", text)[0])
            self.assertFalse(validate_word("-!", text)[0])
            self.assertFalse(validate_word("-?", text)[0])
            self.assertFalse(validate_word("-'", text)[0])

    def test_ordinary_words(self):
        #TODO: implement test_ordinary_words
        pass

class ValidateTitleTestCase(TestCase):
    #TODO: Should I test more exhaustively for disallowed characters?
    # TODO: Should I disallow using spaces in stupid ways (like some of the valid tests right now?)
    def test_empty(self):
        self.assertFalse(validate_title(""))

    def test_no_letters(self):
        self.assertFalse(validate_title(" "))
        self.assertFalse(validate_title("       "))
        self.assertFalse(validate_title("9"))
        self.assertFalse(validate_title("0"))
        self.assertFalse(validate_title("130 3940"))

    def test_valid(self):
        self.assertTrue(validate_title("a"))
        self.assertTrue(validate_title("Title"))
        self.assertTrue(validate_title("Rambo 9"))
        self.assertTrue(validate_title("7 Samurai"))
        self.assertTrue(validate_title("The end of the world"))
        self.assertTrue(validate_title("a       "))
        self.assertTrue(validate_title("X9134457914 390281795"))
        self.assertTrue(validate_title("a       "))
        self.assertTrue(validate_title("a       "))

    def test_disallowed_characters(self):
        self.assertFalse(validate_title("a ."))
        self.assertFalse(validate_title("a ,"))
        self.assertFalse(validate_title("a '"))
        self.assertFalse(validate_title("a \""))
        self.assertFalse(validate_title("a ["))
        self.assertFalse(validate_title("a {"))
        self.assertFalse(validate_title("a <"))

# NOTE: Experimental testing of starting a new story
# NOTE: I could not get this working. May return to it but I'm going to try to 
# just fix the bug instead for now
# class IndexChannelTestCase(TestCase):
#     async def test_auth(self):
#         user = User.objects.create_user('test_user')
#         communicator = WebsocketCommunicator(asgi_app, "/ws/circle_index/")
#         communicator.scope['user'] = user
#         connected, subprotocol = await communicator.connect()
#         self.assertTrue(connected)
#         self.assertEquals(communicator.instance.scope['user'], user)
#         communicator.disconnect()

#     async def test_valid_title(self):
#         pass
