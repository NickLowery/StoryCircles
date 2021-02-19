import re
import string

def validate_word(word, text):
    """Check if something is a valid "word" submission with previous existing text.
    Return (valid, formatted_word, message), where valid is a boolean, formatted_word is
    the word ready to be added to existing text (adding a space if applicable for example), and
    message is an error message if the word was not valid.
    It can be a word, or ?, !, . for now. Can make it a little more complicated later."""
    if not text:
        if re.fullmatch("[a-zA-Z']+", word):
            return (True, string.capwords(word), "")
        else:
            return (False, "", "Story must begin with a word")
    if word == "":
        return (False, "", "You have to write something!")
    if re.fullmatch("[a-zA-Z']+", word):
        if text[-1] in ["?", ".", "!", "\n"]:
            return (True, (' ' + string.capwords(word)), "")
        else:
            return (True, (' ' + word), "")
    if re.fullmatch("\-[a-zA-Z']+", word):
        if not text[-1].isalpha():
            return (False, "", "You can only hyphenate after a word.")
        if re.search("\-'", word):
            return(False, "", "An apostrophe cannot directly follow a hyphen.")
        else:
            return (True, word, "")
    if re.search(",", word):
        if re.fullmatch(", [a-zA-Z']+", word):
            if text[-1].isalpha():
                return (True, word, "")
            else:
                return (False, "", "A comma can only come after a word.")
        else:
            return (False, "", "Invalid comma use.")
    if word in ["?", ".", "!"]:
        if text[-1].isalpha():
            return (True, word, "")
        else:
            return (False, "", "Sentence-ending punctuation can only go after a word.")
    if " " in word:
        return (False, "", "Word cannot contain spaces except after a comma.")
    else:
        return (False, "", "Not a valid word for some reason (disallowed characters?)")

def validate_title(title):
    """Check if a story title is valid. It needs to contain at least one letter and nothing but
    letters, digits, and spaces. Return True if valid, False if not"""
    if re.search("^ ", title) or re.search("  ", title) or re.search(" $", title):
        return False
    elif re.search("[a-zA-Z]", title) and re.fullmatch("[a-zA-Z0-9\ ]+", title):
        return True
    else:
        return False
