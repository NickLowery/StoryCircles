// TODO: Real naming of circles? Some kind of matchmaking.
const circleName = 'mockupCircle';
const username = JSON.parse(document.getElementById('user-data').textContent);
const wordInputDom = document.getElementById('word-input');
const wordSubmitDom = document.getElementById('word-submit');

const circleSocket = new WebSocket(
  'ws://'
  + window.location.host
  + '/ws/circle/'
  + circleName
  + '/'
);

circleSocket.onmessage = function(e) {
  const data = JSON.parse(e.data);
  console.log(data);

  switch (data.type) {
    case ('game_update'): 
      // Update game display
      document.querySelector("#text").innerHTML = data.text;
      document.querySelector("#dev-turn-order").innerHTML = data.turn_order;
      // Only allow input if it's our turn
      if (username === data.turn_order[0]) {
        // console.log("my turn");
        wordInputDom.style.display = "inline-block";
        wordSubmitDom.style.display = "inline-block";
      }
      else {
        wordInputDom.style.display = "none";
        wordSubmitDom.style.display = "none";
      }
      break;
    case ('message'):
      // Display message in an alert
      console.log("Message: " + data.message_text);
      const alertTemplateDom = document.querySelector("#alert-template");
      const alert = alertTemplateDom.cloneNode(true);
      const alertText = alert.querySelector("#alert-text");
      alertText.innerHTML = data.message_text;
      document.querySelector("#alert-holder").appendChild(alert);
      alert.style.display = "block";
      break;
    default:
      console.error("Default hit on socket message type")
  }
};

circleSocket.onclose = function(e) {
  console.error('Circle socket closed unexpectedly');
}

wordInputDom.focus();
wordInputDom.onkeyup = function(e) {
  if (e.keyCode === 13) { // enter, return
    wordSubmitDom.click();
  }
};

wordSubmitDom.onclick = function(e) {
  
  const word = wordInputDom.value;
  //TODO: Client-side checking of submission
  circleSocket.send(JSON.stringify({
    'type': 'word_submit',
    'word': word
  }));
  wordInputDom.value = '';
};

document.querySelector("#propose-end").onclick = function(e) {
  circleSocket.send(JSON.stringify({
    'type': 'propose_end',
  }));
}
