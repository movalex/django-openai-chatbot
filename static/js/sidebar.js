const sidebarWrapper = document.getElementById('sidebar-wrapper');
const sidebarToggle = document.body.querySelector('#sidebarToggle');
const closeSidebar = document.body.querySelector('#closeSidebarButton');
var csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

function createNewChatRoom() {
    // Retrieve the CSRF token from the document

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
        anchor.setAttribute('data-chat-id', room.id);
        anchor.className = 'list-group-item list-group-item-action list-group-item-light p-3';

        // Create a container for the span and the button
        const container = document.createElement('div');
        container.style.display = 'flex';
        container.style.justifyContent = 'space-between';
        container.style.width = '100%';
        container.style.alignItems = 'center';

        const span = document.createElement('span');
        span.className = 'chat-name small';
        span.setAttribute('contenteditable', 'false');
        // Make the span take up the remaining space and center its content
        span.style.flexGrow = '1';
        span.style.textAlign = 'left';
        span.textContent = room.name;

        const button = document.createElement('button');
        button.className = 'btn btn-link border-0 p-0 archive-chat-btn';
        button.type = 'button';

        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', '24');
        svg.setAttribute('height', '24');
        svg.setAttribute('viewBox', '0 0 20 20');
        svg.setAttribute('fill', 'currentColor'); // Change color using CSS

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', 'M3.62188 3.07918C3.87597 2.571 4.39537 2.25 4.96353 2.25H13.0365C13.6046 2.25 14.124 2.571 14.3781 3.07918L15.75 5.82295V13.5C15.75 14.7426 14.7426 15.75 13.5 15.75H4.5C3.25736 15.75 2.25 14.7426 2.25 13.5V5.82295L3.62188 3.07918ZM13.0365 3.75H4.96353L4.21353 5.25H13.7865L13.0365 3.75ZM14.25 6.75H3.75V13.5C3.75 13.9142 4.08579 14.25 4.5 14.25H13.5C13.9142 14.25 14.25 13.9142 14.25 13.5V6.75ZM6.75 9C6.75 8.58579 7.08579 8.25 7.5 8.25H10.5C10.9142 8.25 11.25 8.58579 11.25 9C11.25 9.41421 10.9142 9.75 10.5 9.75H7.5C7.08579 9.75 6.75 9.41421 6.75 9Z');

        svg.appendChild(path);
        button.appendChild(svg);

        // Append span and button to the container
        container.appendChild(span);
        container.appendChild(button);

        // Append the container to the anchor
        anchor.appendChild(container);

        listGroup.appendChild(anchor);

        // If the room's ID/UUID matches the current URL, add the 'active-chatroom' class
        if(room.id === chatRoomIdOrUuid) {
            anchor.classList.add('active-chatroom');
            anchor.addEventListener('click', function(event) {
                event.preventDefault(); // Prevent navigation on click
            })
        };
        listGroup.appendChild(anchor);
        // Add event listener for double-click
        span.addEventListener('dblclick', function() {
            handleDoubleClickRename(span, room.id);
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
            console.error('Fetch ChatRooms error:', e);
        });
}


async function saveNewName(chatId, newName) {
    // Implement the AJAX call to save the new name to the backend
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
    const currentName = chatItem.textContent;
    chatItem.setAttribute("contentEditable", "true");
    chatItem.focus();
    // Event listener for pressing Enter key
    chatItem.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            console.log("Enter")
            this.blur(); // Triggers the blur event
        }
    });
    chatItem.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            console.log("Escape")
            this.textContent = currentName;
            this.blur(); // Triggers the blur event
        }
    });

    chatItem.addEventListener('blur', function() {
        const newName = this.textContent.trim();
        if (newName && newName !== currentName) {
            // Save the new name
            saveNewName(chatId, newName).then(() => {
                // Update the UI with the new name
                this.textContent = newName;
            }).catch(error => {
                console.error('Error updating chat name:', error);
            });
        } else {
            // No change or empty name, revert to the old name
            this.textContent = currentName;
        };
    });

    // const input = document.createElement('input');
    // input.type = 'text';
    // input.value = currentName;
    // input.className = 'form-control chat-name-input';  // TODO: adjust styling

    // // Replace the name element with the input field
    // chatItem.replaceChild(input, nameElement);
    // // Focus the input and select the text
    // input.focus();
    // input.select();

    // input.addEventListener('mousedown', function(e) {
    //     e.stopPropagation();
    // });
    // // Define behavior for input blur (losing focus)
    // input.addEventListener('click', function(e) {
    //     e.stopPropagation();
    // });


    // // Event listener for pressing Enter key
    // input.addEventListener('keydown', function(e) {
    //     if (e.key === 'Enter') {
    //         console.log("Enter")
    //         this.blur(); // Triggers the blur event
    //     }
    // });
    // input.addEventListener('keydown', function(e) {
    //     if (e.key === 'Escape') {
    //         console.log("Escape")
    //         this.value = currentName;
    //         this.blur(); // Triggers the blur event
    //     }
    // });
    
    // input.addEventListener('dblclick', function(e) {
    //     this.focus();
    //     this.select();
    // });
    
    // input.addEventListener('blur', function() {
    //     const newName = this.value.trim();
    //     if (newName && newName !== currentName) {
    //         // Save the new name
    //         saveNewName(chatId, newName).then(() => {
    //             // Update the UI with the new name
    //             nameElement.textContent = newName;
    //         }).catch(error => {
    //             console.error('Error updating chat name:', error);
    //         });
    //     };
    //     chatItem.replaceChild(nameElement, input);
    // });
};


function hideSidebarElement(element, chatId) {


    // Call the backend to hide the chat room
    fetch(`/archive_chat_room/${chatId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            // Include CSRF token as needed for Django
            'X-CSRFToken': csrftoken
        }
    }).then(response => {
        if (response.ok) {
            // Hide the element on successful response
            fetchChatRooms();
        } else {
            console.error('Failed to archive chat room');
        }
    }).catch(error => console.error('Error:', error));
}


document.addEventListener('DOMContentLoaded', function() {
    fetchChatRooms();
    toggleSidebarOnLoad();
    toggleSidebarButtonVisibility();
    
    document.getElementById('list-group').addEventListener('click', function(event) {
        const clickedElement = event.target;
    
        // Check if the clicked element or its parent is a hide button
        if (clickedElement.classList.contains('archive-chat-btn') || clickedElement.closest('.archive-chat-btn')) {
            event.preventDefault(); // Prevent default anchor action
            event.stopPropagation();
            // chatRoomIdOrUuid = currentPath.split('/')[2];
            const chatId = clickedElement.closest('.list-group-item').getAttribute('data-chat-id');
            console.log('Hide button clicked for room:', chatId);

            hideSidebarElement(this.parentElement, chatId);
            // Implement hide logic here
        }
        // Check if a chat room item was clicked
        else if (clickedElement.classList.contains('list-group-item') || clickedElement.closest('.list-group-item')) {
            const chatId = clickedElement.getAttribute('data-room-id') || clickedElement.closest('.list-group-item').getAttribute('data-chat-id');
            console.log('Chat room clicked:', chatId);
            // Implement navigation or other logic here, preventing default if necessary
            // event.preventDefault();
        }
    });
});