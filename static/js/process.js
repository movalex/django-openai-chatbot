let form = document.querySelector(".submit-form")
let input = document.querySelector("#input_value")
// WIP add grow upwards on form input
// input.addEventListener('input', function () {
//   this.style.height = 'auto'; // Reset height
//   this.style.height = (this.scrollHeight) + 'px'; // Set new height
// });

const chatContainer = document.querySelector(".chat-container");
const scrollContainer = document.querySelector(".container-fluid-2");

// Handle keydown event on the input field
input.addEventListener('keydown', function (event) {
  if (event.key === 'Enter') {
    event.preventDefault(); // Prevent default form submission
    if (isMobileDevice() || event.shiftKey) {
      // On mobile devices or when Shift+Enter is pressed, insert a new line
      input.value += "\n";
    } else {
      // On non-mobile devices, when only Enter is pressed, submit the form
      triggerFormSubmit(); // Manually trigger form submission
    }
  }
});

// Function to detect mobile device
function isMobileDevice() {
  return /Mobi|Android/i.test(navigator.userAgent);
}

form.addEventListener("submit", submitForm)

const button = document.getElementById('submit-btn');
const spinner = button.querySelector('.spinner-border');
const icon = button.querySelector('.fa-paper-plane');

// Function to manually trigger form submission
function triggerFormSubmit() {
  // Show the spinner and hide the icon
  toggleSpinner(true)
  let event = new Event('submit', {
    'bubbles': true,
    'cancelable': true
  });
  form.dispatchEvent(event);
}

async function submitForm(e) {

  e.preventDefault(); // Prevent default form submission
  const userMessage = input.value.trim();
  if (userMessage === '') return; // Prevent empty messages

  // Add user message to chat
  addUserMessage(userMessage);
  input.value = ''; // Clear input field
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

  console.log("selected ", selectedModel)
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
  loadHighlightJs();
  return result.response;
}

function scrollToBottom() {
  scrollContainer.scrollTop = scrollContainer.scrollHeight;
}
