let form = document.querySelector(".submit-form")
let input_textarea = document.querySelector("#chat-input")
let scrollButton = document.querySelector("#scrollToBottomBtn")
let chatContainer = document.querySelector(".chat-container");
const mainContainer = document.querySelector('.main-chat-body');

function adjustButtonPadding() {

  if (mainContainer && scrollButton) {
      const containerRect = mainContainer.getBoundingClientRect();
      const windowHeight = window.innerHeight;
      const bottomPadding = windowHeight - (containerRect.bottom);
      scrollButton.style.bottom = (20 + bottomPadding) + `px`;
  }
}

// Function to auto-expand the textarea
function autoAdjustTextarea() {
  input_textarea.style.height = 'auto'; // Reset height
  input_textarea.style.height = (input_textarea.scrollHeight) + 'px'; // Set new height

  // Calculate the additional height beyond the default height of the textarea
  const additionalHeight = input_textarea.clientHeight;
  // Adjust the bottom offset of the scroll button
  adjustButtonPadding() 
}

function checkScroll() {
  const scrollContainer = document.querySelector(".main-chat-body");
  const chatList = document.querySelector(".chat-container");
  
  // Check if the container is scrolled to the bottom

  const offset = 5;
  if (scrollContainer.scrollHeight - scrollContainer.scrollTop <= scrollContainer.clientHeight + offset) {
      // Hide the button if scrolled to the bottom
      scrollButton.style.display = 'none';
  } else {
      // Show the button if not scrolled to the bottom
      scrollButton.style.display = 'block';
  }
  // Show or hide the button based on the chat list content
  if (chatList.clientHeight === 0 || scrollContainer.scrollHeight <= scrollContainer.clientHeight) {
    scrollButton.style.display = 'none'; // Hide the scroll button if the chat list is empty or if there's no scrollbar
  }

}

// Event listener for scrolling in the container
mainContainer.addEventListener('scroll', checkScroll);

// Adjust the height on load and when the window is resized
window.addEventListener('load', adjustButtonPadding);
window.addEventListener('resize', adjustButtonPadding);

// Event listener to trigger auto-expand on input
input_textarea.addEventListener('input', autoAdjustTextarea);

// Handle keydown event on the input field
document.addEventListener('DOMContentLoaded', function () {
  input_textarea.addEventListener('keydown', function (event) {
    if (event.key === 'Enter') {
      event.preventDefault(); // Prevent default form submission
      if (isMobileDevice() || event.shiftKey) {
        insertAtCursor(input_textarea, '\n'); // Insert a newline at the cursor position
        autoAdjustTextarea(); // Update the height when "Enter" is pressed
      } else {
        // On non-mobile devices, when only Enter is pressed, submit the form
        triggerFormSubmit(); // Manually trigger form submission
      }
    }
  });
});

// Function to insert text at the current cursor position in a textarea
function insertAtCursor(myField, myValue) {
  // IE support
  if (document.selection) {
      myField.focus();
      const sel = document.selection.createRange();
      sel.text = myValue;
  }
  // Mozilla and Webkit support
  else if (myField.selectionStart || myField.selectionStart == '0') {
      const startPos = myField.selectionStart;
      const endPos = myField.selectionEnd;
      myField.value = myField.value.substring(0, startPos)
          + myValue
          + myField.value.substring(endPos, myField.value.length);
      myField.selectionStart = startPos + myValue.length;
      myField.selectionEnd = startPos + myValue.length;
  } else {
      myField.value += myValue;
  }
}

// Function to detect mobile device
function isMobileDevice() {
  return /Mobi|Android/i.test(navigator.userAgent);
}


// FORM SUBMIT SCRIPTS

form.addEventListener("submit", submitForm)

const button = document.getElementById('submit-btn');
const spinner = button.querySelector('.spinner-border');
const icon = button.querySelector('.fa-square-arrow-up-right');

// Function to manually trigger form submission
function triggerFormSubmit() {
  // Show the spinner and hide the icon
  let event = new Event('submit', {
    'bubbles': true,
    'cancelable': true
  });
  form.dispatchEvent(event);
}

async function submitForm(e) {

  e.preventDefault(); // Prevent default form submission
  const userMessage = input_textarea.value.trim();
  if (userMessage === '') return; // Prevent empty messages
  toggleSpinner(true)
  // Add user message to chat
  addUserMessage(userMessage);
  input_textarea.value = ''; // Clear input field
  input_textarea.style.height = 'auto'; // Reset height
  scrollToBottom();

  try {
    const response = await fetchBotResponse(userMessage);
    // Add bot response to chat
    addBotResponse(response);
    scrollToBottom();
  } catch (error) {
    console.error(error);
  }
  finally {
    toggleSpinner(false);
  }
}

function toggleSpinner(isLoading) {
  spinner.style.display = isLoading ? "inline-block" : "none";
  icon.style.display = isLoading ? 'none' : 'flex';
  // Optionally, disable the button to prevent multiple submissions
  button.disabled = isLoading;
}

function addUserMessage(message) {
  const userMessageDiv = document.createElement("div");
  userMessageDiv.className = "user-chat-container";
  userMessageDiv.innerHTML = `
  <div class="user-pic"><i class="fa-solid fa-circle-user"></i></div>
  <div class="user-message">${message}</div>
  `
  chatContainer.appendChild(userMessageDiv);
}

function addBotResponse(response) {
  const userBotDiv = document.createElement("div");
  userBotDiv.className = "bot-chat-container";
  userBotDiv.innerHTML = `
  <div class="bot-icon"><i class="fa-solid fa-robot"></i></div>
  <div class="bot-response">${response}</div>
  `
  chatContainer.appendChild(userBotDiv)
}

async function fetchBotResponse(userMessage) {

  spinner.style.display = "flex"
  const url = ""
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  const selectedModel = document.getElementById('modelIdField').value; // Get the value of the hidden field

  const response = await fetch(url, {
    method: "POST",
    body: new URLSearchParams({
      'csrfmiddlewaretoken': csrfToken,
      'message': userMessage,
      'model_id': selectedModel, // Include the selectedModel value in the POST request
    }),
  });
  const result = await response.json();
  if (!response.ok) {
    const errorMessage = result.error || `HTTP error! Status: ${response.status}`;
    alert(errorMessage);
    throw new Error(`HTTP error! Status: ${response.status}\n Error Message: ${errorMessage}`);
  }
  spinner.style.display = "none";
  scrollToBottom();
  loadHighlightJs();
  return result.response;
}
window.addEventListener('load', scrollToBottom);


function scrollToBottom() {
    mainContainer.scrollTop = mainContainer.scrollHeight;
}
scrollButton.addEventListener('click', scrollToBottom);

