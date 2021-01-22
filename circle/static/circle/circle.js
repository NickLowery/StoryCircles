const circlePk = document.getElementById('data-div').dataset['circlepk'];
const username = JSON.parse(document.getElementById('user-data').textContent);
const wordInputDom = document.getElementById('word-input');
const wordSubmitDom = document.getElementById('word-submit');
const endingApprovalDom = document.getElementById('ending-approval-div');
const proposeEndDom = document.getElementById('propose-end-button');

const circleSocket = new WebSocket(
  'ws://'
  + window.location.host
  + '/ws/circle/'
  + circlePk
  + '/'
);

circleSocket.onmessage = function(e) {
  const data = JSON.parse(e.data);
  console.log(data);

  switch (data.type) {
    case ('game_update'): 
      if (!data.story_started) {
        document.getElementById('current-author-count').innerHTML = data.turn_order.length;
      }
      else {
        // Game is started
        document.getElementById('game-div').style.display = "block";
        document.getElementById('waiting-div').style.display = "none";
        // Update game display
        document.querySelector("#text").innerHTML = data.text;
        document.querySelector("#dev-turn-order").innerHTML = data.turn_order;
        // Only allow input and ending if it's our turn
        if (username === data.turn_order[0]) {
          // Only allow input if no ending is proposed
          if (!data.approved_ending_list.length) {
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
          hideWordInput();
          hideProposeEnd();
        }
        
        // Allow approving or rejecting an ending if one was proposed and we
        // haven't approved it.
        if (data.approved_ending_list.length 
              && !data.approved_ending_list.includes(username)) {
          endingApprovalDom.style.display = "block";
        } else {
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
    case ('story_finished'):
      alert_message("Story finished! Going to its permanent home in 5 seconds");
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

