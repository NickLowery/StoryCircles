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
    'word': word
  }));
  wordInputDom.value = '';
};
