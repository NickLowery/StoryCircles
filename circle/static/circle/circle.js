const circlePk = document.getElementById('data-div').dataset['circlepk'];
const username = JSON.parse(document.getElementById('user-data').textContent);
const wordInputDom = document.getElementById('word-input');
const wordSubmitDom = document.getElementById('word-submit');
const endingApprovalDom = document.getElementById('ending-approval-div');
const proposeEndDom = document.getElementById('propose-end-button');
const statusBarDom = document.getElementById('story-status-div');

const circleSocket = new WebSocket(
  'ws://'
  + window.location.host
  + '/ws/circle/'
  + circlePk
  + '/'
);

const thresholdUserCt = parseInt(document.getElementById('data-div').dataset.thresholdUserCt);

circleSocket.onmessage = function(e) {
  const data = JSON.parse(e.data);
  console.log(data);

  switch (data.type) {
    case ('game_update'): 
      if (!data.story_started) {
        setStatusBar(`${thresholdUserCt} authors needed to start the story. Waiting for ${thresholdUserCt - data.turn_order.length} more!`);
      }
      else {
        // Game is started
        document.getElementById('game-div').style.display = "block";
        // Update game display
        document.querySelector("#text").innerHTML = data.text;
        document.querySelector("#dev-turn-order").innerHTML = data.turn_order;
        const whoseTurn = data.turn_order[0];
        // TODO: Restructure this logic. It's super messy. Cover proposed ending first? It doesn't matter
        // whose turn it is if an ending is proposed actually.
        // Only allow input and ending if it's our turn
        if (username === whoseTurn) {
          // Only allow input if no ending is proposed
          if (!data.approved_ending_list.length) {
            setStatusBar("Your turn!");
            showWordInput();
          }
          else {
            hideWordInput();
          }

          // You can propose ending the story on your turn, if it's not proposed and
          // there's at least some text in the story.
          if (data.text !== "" && !data.approved_ending_list.length) {
            showProposeEnd();
          }
          else {
            hideProposeEnd();
          }
        }
        else {
          setStatusBar(`${whoseTurn}'s turn`);
          hideWordInput();
          hideProposeEnd();
        }
        
        // Allow approving or rejecting an ending if one was proposed and we
        // haven't approved it.
        if (data.proposed_ending === username) {
          setStatusBar("You proposed ending the story. Waiting for other users.");
          endingApprovalDom.style.display = "none";
        }
        else if (data.proposed_ending) { 
          if (data.approved_ending_list.includes(username)) {
            setStatusBar(`${data.proposed_ending} proposed ending the story here and you approved.`);
            endingApprovalDom.style.display = "none";
          }
          else {
          setStatusBar(`${data.proposed_ending} proposed ending the story here.`);
            endingApprovalDom.style.display = "block";
          } 
        } 
        else {
          endingApprovalDom.style.display = "none";
        }
      }

      if (data.message) {
        alert_message(data.message);
      }
      break;
    case ('message'):
      // Display message in an alert
      alert_message(data.message_text);
      break;
    case ('redirect'):
      alert_message(data.message_text);
      setTimeout(() => {
        window.location.href = data.redirect_url;
      }, 5000);
      break;
    default:
      console.error("Default hit on socket message type")
  }
};

circleSocket.onclose = function(e) {
  console.error('Circle socket closed unexpectedly');
}

function showWordInput() {
  wordInputDom.style.display = "inline-block";
  wordSubmitDom.style.display = "inline-block";
  wordInputDom.focus();
}

function setStatusBar(status_string) {
  statusBarDom.innerHTML = status_string;
}

function hideWordInput() {
  wordInputDom.style.display = "none";
  wordSubmitDom.style.display = "none";
}

function showProposeEnd() {
  document.querySelector("#propose-end-button").style.display = "block";
}

function hideProposeEnd() {
  document.querySelector("#propose-end-button").style.display = "none";
}

wordInputDom.onkeyup = function(e) {
  if (e.keyCode === 13) { // enter, return
    wordSubmitDom.click();
  }
};

wordSubmitDom.onclick = function(e) {
  const word = wordInputDom.value;
  circleSocket.send(JSON.stringify({
    'type': 'word_submit',
    'word': word
  }));
  wordInputDom.value = '';
};

document.querySelector("#approve-end-button").onclick = function(e) {
  circleSocket.send(JSON.stringify({
    'type': 'approve_end',
  }));
}

document.querySelector("#reject-end-button").onclick = function(e) {
  circleSocket.send(JSON.stringify({
    'type': 'reject_end',
  }));
}

document.querySelector("#propose-end-button").onclick = function(e) {
  circleSocket.send(JSON.stringify({
    'type': 'propose_end',
  }));
}

