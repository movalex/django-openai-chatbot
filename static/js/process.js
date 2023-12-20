let form = document.querySelector(".submit-form")
let input = document.querySelector("#input_value")

const chatContainer = document.querySelector(".chat-container");
let spinner = document.querySelector(".spinner-main")

form.addEventListener("submit", submitForm)

async function submitForm(e) {
  e.preventDefault();
  const userMessage = input.value.trim();
  if (userMessage === '') return; // Prevent empty messages
  scrollToBottom();
  // Add user message to chat
  addUserMessage(userMessage);
  input.value = ''; // Clear input field

  try {
    const response = await fetchBotResponse(userMessage);
    // Add bot response to chat
    addBotResponse(response);
    scrollToBottom();
  } catch (error) {
    console.error("Error:", error);
    alert(error.message); // User-friendly error message
  }

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

  const response = await fetch(url, {
    method: "POST",
    body: new URLSearchParams({
      'csrfmiddlewaretoken': csrfToken,
      'message': userMessage
    }),
  });
  const result = await response.json();
  console.log(result)
  if (!response.ok) {
    const errorMessage = response.error || `HTTP error! Status: ${response.status}`;
    throw new Error(`HTTP error! Status: ${response.status}\n Error Message: ${errorMessage}`);
  }
  spinner.style.display = "none"
  return result.response;
}

function scrollToBottom() {
  chatContainer.scrollTop = chatContainer.scrollHeight;
}