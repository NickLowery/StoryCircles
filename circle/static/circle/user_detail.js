if (document.getElementById('data-div').dataset['isthisme'] === "true") {
  // Set nav style
  let currentNav = document.getElementById('current-user-nav');
  currentNav.classList.add("active");
  currentNav.setAttribute("aria-current", "page");
}
