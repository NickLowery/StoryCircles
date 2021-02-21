function alertMessage(message) {
  // Display message in an alert
  console.log("Message: " + message);
  const alertTemplateDom = document.querySelector("#alert-template");
  const alert = alertTemplateDom.cloneNode(true);
  const alertText = alert.querySelector("#alert-text");
  alertText.innerHTML = message;
  document.querySelector("#alert-holder").appendChild(alert);
  alert.style.display = "block";
  window.setTimeout(function(){
    alert.style.animationPlayState = 'running';
    alert.addEventListener('animationend', function() {
      alert.remove();
    });
  }, 3000);
}
