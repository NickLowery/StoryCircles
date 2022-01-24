"StoryCircles"
=========
Nick Lowery 2021
---------------

### What is it?

Have you ever played the game where a group of people take turns contributing 
single words to write a story? StoryCircles is a chatroom-like web 
implementation of that game. Users can register, log in, and then start or join 
a "Circle" where they play the game. 

All the users are updated in real time with other users' input in their Circle.

The app also provides users the ability to see a list of finished stories and 
read them, as well as very basic author profile pages with a list of stories the 
author participated in writing. 

That's about it!

### How does the game work?

- Users take turns typing one word. 
- You can also use your turn to end a sentence with a period, question mark, or 
    exclamation mark.
- You can put a comma between the previous word and your word.
- You can hyphenate another word onto the previous word, and this is the only 
    way hyphenated words can be formed.
- No punctuation is allowed in this version, except for the marks mentioned 
  above, and apostrophes.
- On your turn, if the previous sentence has ended, you can propose a paragraph 
    break or ending the story. Unanimous consent is required for either. This is 
    how my friends and I used to play the game.

StoryCircles doesn't attempt to check that "words" are real words, or that 
grammar makes sense, etc. It just tries to make sure that punctuation can only 
be used according to these rules and that the typography will make sense in the 
context of words and allowed punctuation, by capitalizing the first word in a 
sentence, making sure there's exactly one space between words, etc.

### Say something about the implementation!

StoryCircles uses websockets (provided on the server side by the 
[Channels](https://github.com/django/channels/) library) to make all this work. 
Circles and Stories are represented by Django models and all the information 
about the state of the game is stored in those models. Channels interfaces with 
the models and communicates with the users through websockets, sending them the 
text of the story and the turn order. Figuring out the state of the GUI for each 
user is done on the client side, from that information.


