const titleInputDom = document.getElementById('title-input');
const titleSubmitDom = document.getElementById('title-submit');
const thresholdUserCtInput = document.getElementById('threshold-user-ct-input');
const maxUserCtInput = document.getElementById('max-user-ct-input');
const username = JSON.parse(document.getElementById('user-data').textContent);

// Set nav style
let currentNav = document.getElementById('write-nav');
currentNav.classList.add("active");
currentNav.setAttribute("aria-current", "page");

const indexSocket = new WebSocket(
  'ws://'
  + window.location.host
  + '/ws/write_index/'
);

indexSocket.onmessage = function(e) {
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
  const thresholdUserCt = thresholdUserCtInput.value;
  const maxUserCt = maxUserCtInput.value;
  titleInputDom.value = '';
  if (title !== "") {
    indexSocket.send(JSON.stringify({
      'type': 'circle_create',
      'title': title,
      'threshold_user_ct': thresholdUserCt,
      'max_user_ct': maxUserCt 
    }));
  }
  else {
    alert_message("Invalid title");
  }
}
