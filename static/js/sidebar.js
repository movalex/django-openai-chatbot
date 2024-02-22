const sidebarWrapper = document.getElementById('sidebar-wrapper');
const sidebarToggle = document.body.querySelector('#sidebarToggle');
const closeSidebar = document.body.querySelector('#closeSidebarButton');

function createNewChatRoom() {
    // Retrieve the CSRF token from the document
    var csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // Set up the request headers
    var headers = new Headers();
    headers.append('Content-Type', 'application/json');
    headers.append('X-CSRFToken', csrftoken);

    // Make the POST request using fetch
    fetch('/create_chat_room/', {
        method: 'POST',
        headers: headers,
        credentials: 'include' // Necessary for including cookies, such as the CSRF token cookie
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Redirect to the new chat room or update the UI accordingly
            window.location.href = `/chatroom/${data.room_id}/`;
        } else {
            // Handle error
            alert("Failed to create a new chat room.");
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert("An error occurred while creating the chat room.");
    });
}

document.getElementById('createChatButton').addEventListener('click', createNewChatRoom);

// Function to check if the sidebar is visible
function isSidebarVisible() {
    // Assuming you use a class to hide the sidebar, e.g., 'toggled'
    return !document.getElementById('sidebar-wrapper').classList.contains('toggled');
}


// Function to toggle the sidebarToggle button visibility
function toggleSidebarButtonVisibility() {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const breakpoint = 768;

    // Check if sidebar is visible or if the window width is less than the breakpoint
    if (!isSidebarVisible() || window.innerWidth < breakpoint) {
        // If the sidebar is hidden or screen width is small, show the toggle button
        sidebarToggle.style.display = 'flex';
    } else {
        // If the sidebar is visible and screen width is large, hide the toggle button
        sidebarToggle.style.display = 'none';
    }
}

function toggleSidebarOnLoad() {
    if (sidebarToggle || closeSidebar) {

        // Add event listener for clicks on the toggle button
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault();
            sidebarWrapper.classList.toggle('toggled');
            sidebarToggle.style.display = 'none';
        });
        closeSidebar.addEventListener('click', event => {
            event.preventDefault();
            sidebarWrapper.classList.toggle('toggled');
            sidebarToggle.style.display = 'flex';
        });
    }
}



// Event listener for window resize
window.addEventListener('resize', toggleSidebarButtonVisibility);


function populateChatRooms(chatRooms) {
    // Clear existing chat rooms
    const listGroup = document.getElementById('list-group');
    listGroup.innerHTML = '';   
    // Append each chat room to the list
    const currentPath = window.location.pathname;
    const chatRoomIdOrUuid = currentPath.split('/')[2];
    chatRooms.forEach(room => {
        const anchor = document.createElement('a');
        anchor.href = `/chatroom/${room.id}/`;  // Update with the correct URL pattern
        anchor.className = 'list-group-item list-group-item-action list-group-item-light p-3';
        const span = document.createElement('span');
        span.className = 'chat-name small'
        anchor.appendChild(span);
        span.textContent = room.name;
        // If the room's ID/UUID matches the current URL, add the 'active-chatroom' class
        if(room.id === chatRoomIdOrUuid) {
            anchor.classList.add('active-chatroom');
                anchor.addEventListener('click', function(event) {
                event.preventDefault(); // Prevent navigation on click
            })
        };
        listGroup.appendChild(anchor);
        // Add event listener for double-click
        anchor.addEventListener('dblclick', function() {
            handleDoubleClickRename(this, room.id);
        });
        
    });
}

function fetchChatRooms() {
    fetch('/get_chat_rooms/')
        .then(response => response.json())
        .then(data => {
            if(data.chat_rooms) {
                populateChatRooms(data.chat_rooms);
            } else {
                console.error('Chat rooms data is missing');
            }
        })
        .catch(e => {
            console.error('Fetch error:', e);
        });
}


function getCurrentChatRoomIdOrUuid() {
    // Extract and return the current chat room ID or UUID from the URL.
    const pathSegments = window.location.pathname.split('/');
    return pathSegments[pathSegments.length - 2]; // Adjust based on your URL structure, assuming the ID or UUID is the second last segment.
}


function handleChatItemClick(event, item) {
    event.preventDefault(); // Always prevent default to manually control navigation

    const href = item.getAttribute('href');
    const chatId = href.split('/')[2]; // Extract the chat ID from the href

    // Check for double click
    if (clickTimer) {
        clearTimeout(clickTimer);
        clickTimer = null;
        // Double-click detected
        enableRenameMode(item, chatId);
    } else {
        clickTimer = setTimeout(() => {
            clickTimer = null;
            // Single click action
            if (chatId !== currentChatRoomId) {
                window.location.href = href; // Navigate only if different chat room
            }
        }, 300); // Adjust threshold as needed
    }
}
async function saveNewName(chatId, newName) {
    // Implement the AJAX call to save the new name to the backend
    var csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    console.log(`Saving new name "${newName}" for chatId ${chatId}`);
    // Example AJAX call (you need to implement this according to your backend)
    fetch('/save_chat_name/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken,
      },
      body: JSON.stringify({ chatId: chatId, newName: newName })
    })
    .then(response => response.json())
    .then(data => {
      if(data.success) {
        // Update the UI accordingly, if necessary
        console.log("Chat name updated successfully.");
      } else {
        console.log("Failed to update chat name.");
      }
    })
    .catch(error => console.error('Error:', error));
  }


function handleDoubleClickRename(chatItem, chatId) {
    const nameElement = chatItem.querySelector('.chat-name');
    const currentName = nameElement.textContent;
    const input = document.createElement('input');
    input.type = 'text';
    input.value = currentName;
    input.className = 'form-control chat-name-input';  // TODO: adjust styling

    // Replace the name element with the input field
    chatItem.replaceChild(input, nameElement);
    // Focus the input and select the text
    input.focus();
    input.select();

    // Define behavior for input blur (losing focus)
    input.addEventListener('blur', function() {
        const newName = input.value.trim();
        if (newName && newName !== currentName) {
            // Save the new name
            saveNewName(chatId, newName).then(() => {
                // Update the UI with the new name
                nameElement.textContent = newName;
                chatItem.replaceChild(nameElement, input);
            }).catch(error => {
                console.error('Error updating chat name:', error);
                // Optionally, revert to the old name on error
                chatItem.replaceChild(nameElement, input);
            });
        } else {
            // No change or empty name, revert to the old name
            chatItem.replaceChild(nameElement, input);
        }
    });
    // Event listener for pressing Enter key
    input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault(); // Prevent form submission if it's part of a form
            input.blur(); // Triggers the blur event
        }
    });

};

document.addEventListener('DOMContentLoaded', function() {
    toggleSidebarOnLoad();
    toggleSidebarButtonVisibility();
    fetchChatRooms();
});