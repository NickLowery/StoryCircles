README.md
=========
"Story Circles"
--------------
Nick Lowery 2021
---------------


### What is it?

Have you ever played the game where a group of people take turns contributing 
single words to write a story? Story Circles is a web implementation of that 
game. Users can register, log in, and then start or join a group (I call it a 
Circle) where they play the game. All the users are updated in real time with 
other users' input in their Circle. Users can only type a word on their turn, 
and the app does some basic enforcement of rules of the game:
- One word at a time
- Ending a sentence with a period, exclamation mark, or question mark uses your turn.
- You can hyphenate another word onto the previous word.
- You can put a comma between the previous word and your word.
- No punctuation is allowed in this version, except for the marks mentioned 
    above, and apostrophes.
- On your turn, if the previous sentence has ended, you can propose a paragraph 
    break or ending the story. Unanimous consent is required for either. This is 
    how my friends and I used to play the game...

The app doesn't attempt to check that "words" are real words, or that grammar 
makes sense, etc. It just tried to make sure that punctuation can only be used 
in reasonable ways and that the typography will make sense in that framework.

The app also provides users the ability to see a list of finished stories and 
read them, as well as very basic author profile pages with a list of stories the 
author participated in writing. 

That's about it! The bulk of the work went into making the real-time writing of 
the story work. It's been fun and challenging.

### How To Run It

### What is in the files (ignoring .gitignore and things I didn't directly edit):

- circle/admin.py
    Just registers a couple models I wanted to be able to edit with the admin 
    app

- circle/consumers.py
    This is where the bulk of my Python code is as it controls all the real-time 
    interaction. There are two classes here, one for the 

- circle/models.py
- circle/routing.py
- circle/static/circle/circle.js
- circle/static/circle/finishedstory_list.js
- circle/static/circle/general.js
- circle/static/circle/index.js
- circle/static/circle/login.js
- circle/static/circle/register.js
- circle/static/circle/styles.css
- circle/static/circle/styles.css.map
- circle/static/circle/styles.scss
- circle/static/circle/user_detail.js
- circle/templates/circle/circle.html
- circle/templates/circle/finishedstory_detail.html
- circle/templates/circle/finishedstory_list.html
- circle/templates/circle/include/finished_story_table.html
- circle/templates/circle/index.html
- circle/templates/circle/layout.html
- circle/templates/circle/login.html
- circle/templates/circle/register.html
- circle/templates/circle/story_text.html
- circle/templates/circle/user_detail.html
- circle/tests.py
- circle/urls.py
- circle/views.py
- storycircles/asgi.py
- storycircles/settings.py
- storycircles/urls.py
- storycircles/wsgi.py
