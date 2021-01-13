const titleInputDom = document.getElementById('title-input');
const titleSubmitDom = document.getElementById('title-submit');
const username = JSON.parse(document.getElementById('user-data').textContent);

const indexSocket = new WebSocket(
  'ws://'
  + window.location.host
  + '/ws/circle_index/'
);

indexSocket.onmessage = function(e) {
  // For now we just log whatever messages we get. Building this out.
  const data = JSON.parse(e.data);
  console.log(data);
  if (data.type === "message") {
    alert_message(data.message_text);
  }
  else if (data.type === "redirect") {
    window.location.href = data.url;
  }

}

indexSocket.onclose = function(e) {
  console.error('Circle socket closed unexpectedly');
}

titleInputDom.focus();
titleInputDom.onkeyup = function(e) {
  if (e.keyCode === 13) { // enter, return
    titleSubmitDom.click();
  }
};

titleSubmitDom.onclick = function(e) {
  const title = titleInputDom.value;
  titleInputDom.value = '';
  // TODO: Title should be alphanumeric as well as non-empty
  if (title !== "") {
    indexSocket.send(JSON.stringify({
      'type': 'circle_create',
      'title': title
    }));
  }
  else {
    alert_message("Invalid title");
  }

}

function alert_message(message) {
      // Display message in an alert
      console.log("Message: " + message);
      const alertTemplateDom = document.querySelector("#alert-template");
      const alert = alertTemplateDom.cloneNode(true);
      const alertText = alert.querySelector("#alert-text");
      alertText.innerHTML = message;
      document.querySelector("#alert-holder").appendChild(alert);
      alert.style.display = "block";
}
