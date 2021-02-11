const circlePk = document.getElementById('data-div').dataset['circlepk'];
const clientUsername = JSON.parse(document.getElementById('user-data').textContent);
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

        // Populate turn order list
        const turnOrderDom = document.querySelector("#turn-order-col");
        const authorTemplate = document.querySelector("#turn-order-author-template");
        for (let orderUsername of data.turn_order) {
          const userDiv = authorTemplate.cloneNode(true);
          userDiv.removeAttribute("id");
          userDiv.innerHTML = orderUsername;
          userDiv.style.display = "block";
          if (orderUsername === clientUsername) {
            userDiv.style.backgroundColor = "chartreuse";
          }
          turnOrderDom.appendChild(userDiv);
        }

        // First deal with any proposed ending that exists because regular input will be 
        // disabled
        if (data.proposed_ending) {
          hideWordInput();
          hideProposeEnd();
          if (data.proposed_ending === clientUsername) {
            setStatusBar("You proposed ending the story. Waiting for other users.");
            endingApprovalDom.style.display = "none";
          }
          else {
            // Someone else has proposed ending the story
            if (data.approved_ending_list.includes(clientUsername)) {
              setStatusBar(`${data.proposed_ending} proposed ending the story here and you approved.`);
              endingApprovalDom.style.display = "none";
            }
            else {
            // Allow approving or rejecting an ending if one was proposed and we
            // haven't approved it.
            setStatusBar(`${data.proposed_ending} proposed ending the story here.`);
              endingApprovalDom.style.display = "block";
            }
          }
        }
        else {
          // Ending is not proposed
          endingApprovalDom.style.display = "none";
          if (clientUsername === whoseTurn) {
              setStatusBar("Your turn!");
              showWordInput();
            // You can propose ending the story on your turn, if it's not proposed and
            // there's at least some text in the story.
            if (data.text !== "") {
              showProposeEnd();
            }
            else {
              hideProposeEnd();
            }
          }
          else {
            // Someone else's turn
            setStatusBar(`${whoseTurn}'s turn`);
            hideWordInput();
            hideProposeEnd();
          }
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

