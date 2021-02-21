"Story Circles"
=========
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
    how my friends and I used to play the game.

The app doesn't attempt to check that "words" are real words, or that grammar 
makes sense, etc. It just tries to make sure that punctuation can only be used 
in reasonable ways and that the typography will make sense in the context of 
words and allowed punctuation.

The app also provides users the ability to see a list of finished stories and 
read them, as well as very basic author profile pages with a list of stories the 
author participated in writing. 

That's about it! The bulk of the work went into making the real-time writing of 
the story work. It's been fun and challenging.

### Is it mobile-responsive?

Yes! It has a nav bar that collapses, columns that collapse into one on the 
Write index page, and a turn order display sidebar that disappears on smaller 
displays.

### How To Run It

### What is in the files (ignoring .gitignore and things I didn't directly edit):

- **circle/models.py**

    Contains all my models.

    *User* just provides a join date and get_absolute_url method to get the 
    user's profile page.

    *Story* tracks text, title, and status of a story, finished or in progress. 
    I tried to encapsulate as much implementation as possible away from the 
    consumer and view code.

    There are three managers for *Circle* that get different querysets and a 
    custom create_circle method for creating a Circle and Story together.

    *Circle* represents the group working on a Story. Importantly, it keeps 
    track of the turn order (which is represented with a list of usernames and 
    stored as JSON), min, max, and current user counts, and proposals to end the 
    story or add a paragraph break.

- **circle/rules.py**
        
    Contains two methods for validating words in the game and story titles.

- **circle/tests.py**

    Contains tests for validating words and titles. I wanted to do automated 
    testing of the websockets code but could not figure out the tooling for 
    doing it. Text validation did seem to be a good place for automated testing 
    to make sure I didn't accidentally break things when I changed the logic.

- **circle/consumers.py**
    
    This is where the bulk of my Python code is as it controls all the real-time 
    websocket interaction using Channels. There are two classes here, 
    *WriteIndexConsumer* and *CircleConsumer*. 

    *WriteIndexConsumer*, for the "Write" page lets a user submit a new story 
    title and checks to see if it's valid before starting a new Circle for them.  
    This could have been achieved with a regular Django view but I originally 
    planned to have real-time updating of the list of ongoing stories, and I 
    want to leave that option open for the future.

    *CircleConsumer* handles all the interaction between a client and an active 
    Circle. It has methods for handling websocket messages from the client, and 
    Channel group messages from other users. A lot of the game logic is also in 
    this file when it didn't seem to make sense to abstract it out further.

- **circle/admin.py**

    Just registers a couple models I wanted to be able to edit with the admin 
    app.

- **circle/forms.py**

    Has my user registration form. I used Django's Forms API because it allowed 
    me to get semi-reasonable password validation for free.

- **storycircles/asgi.py** and **circle/routing.py**

    Routing information for the websocket code.

- **storycircles/wsgi.py**, **circle/urls.py**, and **storycircles/urls.py**

    Routing information for the regular Django views

- **storycircles/settings.py**

    Has a few settings changed to make the websocket routing and Redis backend 
    for Channels work.

- **circle/views.py**

    All my regular Django views are here. My index view serves the Write page 
    where the user can start or join a Circle and calls up two querysets of 
    Circles. Otherwise, all the views except for registering and logging in are 
    very simple and use Django's generic class-based views.

- **circle/static/circle/circle.js**

    Client-side code for interactively writing a story in a Circle. Most of the 
    logic is in the gameUpdate function and decides when to show inputs based on 
    the state of the game.

- **circle/static/circle/index.js**

    For the Write page, uses a websocket to send title proposals to the server 
    for validation and displays any messages that come back.

- **circle/static/circle/general.js**

    Just provides an alertMessage function that index.js and circle.js both use 
    to display Bootstrap alerts for certain messages from the server.

- **circle/static/circle/finishedstory_list.js**, 
  **circle/static/circle/login.js**, **circle/static/circle/register.js**, and 
  **circle/static/circle/user_detail.js**

    The only thing these files do is tag the appropriate nav bar option as 
    active for their respective pages.

- **circle/static/circle/styles.css**, **circle/static/circle/styles.css.map**, 
    and **circle/static/circle/styles.scss**

    Along with Bootstrap these provide all my styling. They set up the hiding of 
    the turn order sidebar in smaller viewports and also provide animation for 
    hiding the alert messages on the Circle and Write pages.

- **circle/templates/circle/circle.html**
- **circle/templates/circle/finishedstory_detail.html**
- **circle/templates/circle/finishedstory_list.html**
- **circle/templates/circle/include/finished_story_table.html**
- **circle/templates/circle/index.html**
- **circle/templates/circle/layout.html**
- **circle/templates/circle/login.html**
- **circle/templates/circle/register.html**
- **circle/templates/circle/story_text.html**
- **circle/templates/circle/user_detail.html**
