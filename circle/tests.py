import itertools
from django.test import TestCase
from .consumers import validate_word

# Create your tests here.

class ValidateWordTestCase(TestCase):
    # TODO: Test all major cases

    def test_title_case(self):
        """After sentence-ending punctuation, the next word should be
        capitalized."""
        self.assertEqual((True, " I"), validate_word("i", "ending.")[:-1])
        self.assertEqual((True, " Island"), validate_word("island", "ending.")[:-1])
        self.assertEqual((True, " I'm"), validate_word("i'm", "ending.")[:-1])

    def test_sentence_ending(self):
        """Sentence-ending should work only by itself and after a word"""
        for punct in [".", "!", "?"]:
            self.assertEqual((True, punct), validate_word(punct, "word")[:-1])
            self.assertEqual((True, punct), validate_word(punct, "isn't")[:-1])
            self.assertEqual((True, punct), validate_word(punct, "lily-livered")[:-1])
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
