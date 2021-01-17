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

titleInputDom.focus();
titleInputDom.onkeyup = function(e) {
  if (e.keyCode === 13) { // enter, return
    titleSubmitDom.click();
  }
};

titleSubmitDom.onclick = function(e) {
  const title = titleInputDom.value;
  titleInputDom.value = '';
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

