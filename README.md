"Story Circles"
=========
Nick Lowery 2021
---------------

### What is it?

Have you ever played the game where a group of people take turns contributing 
single words to write a story? Story Circles is a web implementation of that 
game. Users can register, log in, and then start or join a group (I call it a 
Circle) where they play the game. 

All the users are updated in real time with other users' input in their Circle.  
Story Circles uses the Channels library to make this work. All the information 
about the state of the game is stored in the Circle model (and the Story model 
for the text) and Channels interfaces with the models and communicates with the 
users through websockets.

Users can only type a word on their turn, and the app does some basic 
enforcement of rules of the game:
- One word per turn
- You can also use your turn to end a sentence with a period, question mark, or 
    exclamation mark.
- You can put a comma between the previous word and your word.
- You can hyphenate another word onto the previous word.
- No punctuation is allowed in this version, except for the marks mentioned 
  above, and apostrophes.
- On your turn, if the previous sentence has ended, you can propose a paragraph 
    break or ending the story. Unanimous consent is required for either. This is 
    how my friends and I used to play the game.

The app doesn't attempt to check that "words" are real words, or that grammar 
makes sense, etc. It just tries to make sure that punctuation can only be used 
according to these rules and that the typography will make sense in the context 
of words and allowed punctuation, by capitalizing the first word in a sentence, 
making sure there's exactly one space between words, etc.

The app also provides users the ability to see a list of finished stories and 
read them, as well as very basic author profile pages with a list of stories the 
author participated in writing. 

That's about it!

### What makes it complex and distinct from the other projects in CS50W?

The most complex and challenging aspect of implementing this project was the 
real-time interaction. This was definitely quite different from anything in the 
course materials or other projects. It was a new API to work with and the logic 
was challenging at first, because one user's interaction needed to trigger 
websocket messages to other users, ideally without a cascade of database hits. 
There were some interesting design questions in deciding how to represent and 
communicate the state of the game. I ended up representing everything at the 
model level in Django, because it seemed like there could be problems with 
inconsistent representations of the state of the game otherwise, and trying to 
send the minimum amount of necessary information at the Channel layer to keep 
all the users up to date.

For example, I had to figure out where to do validation of word submissions. 
Each user in a circle has an instance of CircleConsumer, which persists as long 
as they're on the Circle's page and controls the websocket connection, and I 
ended up deciding on the client-side to let clients send basically anything as a 
submission and have it get validated at the level of their CircleConsumer. That 
way the server isn't ever adding text to the database that hasn't been evaluated 
by server-side code, and the rest of the users only get a message once the 
submission has been validated and the whole game state is updated on the server.

It would be possible to do the validation on the client-side as well, and have 
less websocket traffic carrying invalid submissions, but the validation logic is 
complicated enough that that seemed like premature optimization.

On the other hand, I left deciding what inputs to show the user up to the 
client-side code, since it would of course control the DOM anyway, and an HTML 
representation of the story text and JSON representation of the turn order was 
sufficient to do that.

### Is it mobile-responsive?

Yes! It has a nav bar that collapses, columns that collapse into one on the 
Write index page, and a turn order display sidebar that disappears on smaller 
displays.

### How To Run It

StoryCircles requires Channels. I ran it with the Redis backend for Channels, in a Docker container (this setup came from Channels tutorials and seems to be the easiest way to get Channels code running).

With pip and git installed and the git repository cloned, I was able to run the app on a new Ubuntu virtual machine by moving to the root of the cloned repository and running the following commands, authenticating and confirming where necessary.

sudo apt-get update
pip3 install -r requirements.txt
sudo apt install docker.io
sudo docker run -p 6379:6379 -d redis:5
python3 manage.py migrate
python3 manage.py runserver

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
    Channel group messages from other users. Managing these messages is the bulk 
    of the work on the app. I tried to design in such a way that a word 
    submission would only trigger queries to the database in the consumer 
    serving the user who submitted the word, then pass all necessary data to the 
    other users through the Channel layer. A lot of the game logic is also in 
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

- **circle/templates/circle/layout.html**

    My main layout template with nav bar and containers for content. I used 
    Bootstrap for the layout utilities and input styling, as well as the 
    collapsible nav bar.

- **circle/templates/circle/circle.html**

    The main writing page. Includes the page of text and all the inputs 
    necessary. It calls circle.js, which takes care of all the interactivity and 
    updating of the game state, and also places the word-input at the end of the 
    last paragraph of text. This also includes the turn order sidebar, which 
    collapses on viewports under a certain width.

- **circle/templates/circle/index.html**

    The "Write" home page which is the default place for users to land when they 
    log in. This has the most complicated layout, which is really only 
    collapsing two columns into one on smaller viewports.  It has the inputs for 
    starting a new story and lists of waiting and started stories the user can 
    join in on.

- **circle/templates/circle/finishedstory_detail.html**

    Template for finished story page. I wanted it to look similar to the Circle 
    page but gave it scriptier fonts for fun.

- **circle/templates/circle/include/finished_story_table.html**

    Simple template for table of finished stories, included by 
    **finishedstory_list.html** and **user_detail.html**

- **circle/templates/circle/finishedstory_list.html**

    Simply lists all finished stories.

- **circle/templates/circle/user_detail.html**

    Very minimal user profile page, since it's not a social network I'm just 
    tracking the join date, and providing a list of stories the user 
    participated in writing.

- **circle/templates/circle/login.html**

    Simple log-in template. If login fails it has a tag to display a message to 
    them, or an alert if they've been redirected here.

- **circle/templates/circle/register.html**

    Simple registration template. It uses Django's Forms API.

- **circle/templates/circle/story_text.html**

    This is a tiny template that gets called inside the Story model to deliver 
    its story as html (to get proper paragraphs). I figured that if I was 
    sending out html through the websocket it would be best to go through 
    Django's template engine, since that way I would also get escaping of 
    special characters and such.

