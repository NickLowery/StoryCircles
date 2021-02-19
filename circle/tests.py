import itertools
from django.test import TestCase
from .rules import validate_word, validate_title
from channels.testing import WebsocketCommunicator
from channels.db import database_sync_to_async
from storycircles.asgi import application as asgi_app
from asgiref.sync import async_to_sync, sync_to_async
from circle.models import User

# Create your tests here.

class ValidateWordTestCase(TestCase):
    def test_simplest_case(self):
        self.assertEqual((True, " expeditiously"), validate_word("expeditiously", "disembarked")[:-1])

    def test_first_word(self):
        self.assertEqual((True, "Expeditiously"), validate_word("expeditiously", "")[:-1])
        self.assertEqual((True, "I"), validate_word("i", "")[:-1])
        self.assertEqual((True, "I"), validate_word("I", "")[:-1])
        self.assertFalse(validate_word(", i", "")[0])
        self.assertFalse(validate_word("-livered", "")[0])
        self.assertFalse(validate_word(".", "")[0])
        self.assertFalse(validate_word(" ", "")[0])
        self.assertFalse(validate_word(" i", "")[0])

    def test_comma(self):
        """After a word, the next 'word' can be of the form ', word'."""
        self.assertEqual((True, ", and"), validate_word(", and", "disembarked")[:-1])
        self.assertEqual((True, ", Robert"), validate_word(", Robert", "disembarked")[:-1])
        self.assertEqual((True, ", hasn't"), validate_word(", hasn't", "disembarked")[:-1])

    def test_invalid_commas(self):
        """Comma should fail anywhere else in a word submission, and followed by or following any punctuation"""
        self.assertFalse(validate_word(",", "text")[0])
        self.assertFalse(validate_word(", ", "text")[0])
        self.assertFalse(validate_word(", ,", "text")[0])
        self.assertFalse(validate_word(", !", "text")[0])
        self.assertFalse(validate_word(", ?", "text")[0])
        self.assertFalse(validate_word(", .", "text")[0])
        self.assertFalse(validate_word(", ..", "text")[0])
        self.assertFalse(validate_word(", -ending", "text")[0])
        self.assertFalse(validate_word(",word", "text")[0])
        self.assertFalse(validate_word(", wo,rd", "text")[0])
        self.assertFalse(validate_word("wo,rd", "text")[0])
        self.assertFalse(validate_word(", and", "ending.")[0])
        self.assertFalse(validate_word(", and", "ending?")[0])
        self.assertFalse(validate_word(", and", "ending!")[0])
        self.assertFalse(validate_word(", and", "")[0])

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
        """Any submission with a space in it other than ', word' should fail"""
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

        # A hyphen inside a word should fail
        self.assertFalse(validate_word("lily-livered", "text")[0])

class ValidateTitleTestCase(TestCase):
    def test_empty(self):
        self.assertFalse(validate_title(""))

    def test_no_letters(self):
        self.assertFalse(validate_title(" "))
        self.assertFalse(validate_title("       "))
        self.assertFalse(validate_title("9"))
        self.assertFalse(validate_title("0"))
        self.assertFalse(validate_title("130 3940"))

    def test_consecutive_spaces(self):
        self.assertFalse(validate_title("Jaws  2"))

    def test_initial_spaces(self):
        self.assertFalse(validate_title(" Jaws 2"))

    def test_final_spaces(self):
        self.assertFalse(validate_title("Jaws 2 "))

    def test_valid(self):
        self.assertTrue(validate_title("a"))
        self.assertTrue(validate_title("Title"))
        self.assertTrue(validate_title("Rambo 9"))
        self.assertTrue(validate_title("7 Samurai"))
        self.assertTrue(validate_title("The end of the world"))
        self.assertTrue(validate_title("X9134457914 390281795"))

    def test_disallowed_characters(self):
        self.assertFalse(validate_title("a ."))
        self.assertFalse(validate_title("a ,"))
        self.assertFalse(validate_title("a '"))
        self.assertFalse(validate_title("a \""))
        self.assertFalse(validate_title("a ["))
        self.assertFalse(validate_title("a {"))
        self.assertFalse(validate_title("a <"))
        self.assertFalse(validate_title("a \n"))
