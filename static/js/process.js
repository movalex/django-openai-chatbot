let form = document.querySelector(".submit-form")
let input = document.querySelector("#input_value")

const chatContainer = document.querySelector(".chat-container");
const scrollContainer = document.querySelector(".container-fluid-2");

let spinner = document.querySelector(".spinner-main")

form.addEventListener("submit", submitForm)

async function submitForm(e) {
  const userMessage = getUserValue();
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
    spinner.style.display = "none"
    console.error(error);
  }
  spinner.style.display = "none"

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

function getUserValue() {
  document.getElementById('input_value').addEventListener('keydown', function (event) {
    if (event.key === 'Enter' && event.shiftKey) {
      console.log("SHIFT enter pressed!");

      // Prevent default Enter behavior only when Shift is also pressed
      event.preventDefault();

      let start = this.selectionStart;
      let end = this.selectionEnd;

      // Insert a newline
      this.value = this.value.substring(0, start) + '\n' + this.value.substring(end);

      // Move the cursor
      this.selectionStart = this.selectionEnd = start + 1;
    }
    else {
      console.log("Just enter pressed!");
      return this.value.trim();
    }
  });

}
