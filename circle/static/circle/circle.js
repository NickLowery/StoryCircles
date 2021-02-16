const circlePk = document.getElementById('data-div').dataset['circlepk'];
const clientUsername = JSON.parse(document.getElementById('user-data').textContent);
const wordInputDom = document.getElementById('word-input');
const wordSubmitDom = document.getElementById('word-submit');
const proposalApprovalDom = document.getElementById('proposal-approval-div');
const proposeEndDom = document.getElementById('propose-end-button');
const statusBarDom = document.getElementById('story-status-div');
const turnOrderDom = document.querySelector("#turn-order-col");
const authorTemplate = document.querySelector("#turn-order-author-template");
const textPage = document.querySelector(".text-page");
const storyTextDom = document.querySelector("#text");

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
      // Populate turn order list
      const whoseTurn = data.turn_order[0];
      turnOrderDom.innerHTML = "";
      data.turn_order.forEach(function (username, index) {
        const userDiv = authorTemplate.cloneNode(true);
        userDiv.removeAttribute("id");
        userDiv.innerHTML = username;
        userDiv.style.display = "block";
        if (username === clientUsername) {
          userDiv.style.backgroundColor = "chartreuse";
        }
        if (index === 0) {
          userDiv.style.fontWeight = "bold";
        }
        turnOrderDom.appendChild(userDiv);
      });
      if (!data.story_started) {
        textPage.style.display = "none";
        setStatusBar(`${thresholdUserCt} authors needed to start the story. Waiting for ${thresholdUserCt - data.turn_order.length} more!`);
        hideProposeEnd();
        hideProposeNewParagraph();
      }
      else {
        // Game is started
        textPage.style.display = "block";
        // Update game display
        storyTextDom.innerHTML = data.text_html;
        storyTextDom.lastChild.appendChild(wordInputDom);


        // First deal with any proposal that exists because regular input will be 
        // disabled
        if (data.active_proposal) {
          prop_string = prop_code_to_string(data.active_proposal);
          hideWordInput();
          hideProposeEnd();
          hideProposeNewParagraph();
          if (data.proposing_user === clientUsername) {
            setStatusBar(`You proposed ${prop_string}. Waiting for other users.`);
            proposalApprovalDom.style.display = "none";
          }
          else {
            // Someone else has proposed ending the story
            if (data.approved_proposal_list.includes(clientUsername)) {
              setStatusBar(`${data.proposing_user} proposed ${prop_string} here and you approved.`);
              proposalApprovalDom.style.display = "none";
            }
            else {
            // Allow approving or rejecting an ending if one was proposed and we
            // haven't approved it.
            setStatusBar(`${data.proposing_user} proposed ${prop_string}; waiting for your response.`);
              proposalApprovalDom.style.display = "block";
              document.querySelector("#approve-button").onclick = () => {
                sendApproval(data.active_proposal)
              };
            }
          }
        }
        else {
          // No proposal active
          proposalApprovalDom.style.display = "none";
          if (clientUsername === whoseTurn) {
            setStatusBar("Your turn!");
            showWordInput();
            // You can propose ending or new paragraph on your turn, if the text ends with
            // a sentence-ending punctuation mark.
            const storyLastP = storyTextDom.lastChild.innerText;
            if ((storyLastP.length > 0) && ["?", "!", "."].includes(storyLastP.charAt(storyLastP.length-1))) {
              showProposeEnd();
              showProposeNewParagraph();
            }
            else {
              hideProposeEnd();
              hideProposeNewParagraph();
            }
          }
          else {
            // Someone else's turn
            setStatusBar(`${whoseTurn}'s turn`);
            hideWordInput();
            hideProposeEnd();
            hideProposeNewParagraph();
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
  wordSubmitDom.style.display = "block";
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

function showProposeNewParagraph() {
  document.querySelector("#propose-new-paragraph-button").style.display = "block";
}

function hideProposeNewParagraph() {
  document.querySelector("#propose-new-paragraph-button").style.display = "none";
}

function sendApproval(prop) {
  circleSocket.send(JSON.stringify({
    'type': 'approve',
    'proposal': prop,
  }));
}

function prop_code_to_string(code) {
  switch (code) {
    case ("ES"):
      return "ending the story";
      break;
    case ("NP"):
      return "starting a new paragraph";
      break;
    default:
      console.error("Unknown proposal code");
  }
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


document.querySelector("#reject-button").onclick = function(e) {
  circleSocket.send(JSON.stringify({
    'type': 'reject',
  }));
}

document.querySelector("#propose-end-button").onclick = function(e) {
  circleSocket.send(JSON.stringify({
    'type': 'propose',
    'proposal': 'ES',
  }));
}

document.querySelector("#propose-new-paragraph-button").onclick = function(e) {
  circleSocket.send(JSON.stringify({
    'type': 'propose',
    'proposal': 'NP',
  }));
}
