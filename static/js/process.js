const messagesList = document.querySelector('.messages-list');
const messageForm = document.querySelector('.submit-form');
const messageInput = document.querySelector('.message-input');

messageForm.addEventListener('submit', (event) => {
  event.preventDefault();

  const message = messageInput.value.trim();
  if (message.length === 0) {
    return;
  }

  // Add the message the user sent to the chat
  const messageItem = document.createElement('li');
  messageItem.classList.add('message', 'sent');
  messageItem.innerHTML = `
      <div class="message-text">
          <div class="message-sender">
              <b>You</b>
          </div>
          <div class="message-content">
              ${message}
          </div>
      </div>`;
  messagesList.appendChild(messageItem);

  // Clear the input field
  messageInput.value = '';

  // Create and add the loading message to the chat
  const loadingMessageItem = document.createElement('li');

  // Create spinner element
  const spinner = document.createElement('div');
  spinner.classList.add('spinner');

  // Append the spinner to the loading message item
  loadingMessageItem.appendChild(spinner);

  // Append the loading message item to the messages list
  messagesList.appendChild(loadingMessageItem);

  // Scroll to the bottom to show the loading message
  scrollToBottom();

  fetch('', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      'csrfmiddlewaretoken': document.querySelector('[name=csrfmiddlewaretoken]').value,
      'message': message
    })
  })
    .then(response => {
      if (!response.ok) {
        // If the response is not OK, read the JSON body and throw an error with the message it contains
        messagesList.removeChild(loadingMessageItem);
        return response.json().then(data => {
          throw new Error(data.error || 'Server error occurred');
        });
      }
      return response.json();
    })
    .then(data => {
      // Remove the loading message from the chat
      messagesList.removeChild(loadingMessageItem);

      // Add the response from the chatbot to the chat
      const response = data.response;
      const responseMessageItem = document.createElement('li');
      responseMessageItem.classList.add('message', 'received');
      responseMessageItem.innerHTML = `
          <div class="message-text">
              <div class="message-sender">
                  <b>AI Chatbot</b>
              </div>
              <div class="message-content">
                  ${response}
              </div>
          </div>`;
      messagesList.appendChild(responseMessageItem);

      // Auto-scroll to the latest message
      scrollToBottom();
    })
    .catch(error => {
      // If there is an error, remove the loading message and possibly show an error message
      alert('An error occurred: ' + error.message);
    });
});

function scrollToBottom() {
  const messagesBox = document.querySelector('.messages-box');
  messagesBox.scrollTop = messagesBox.scrollHeight;
}
scrollToBottom();