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

function toggleSidebarOnLoad() {

        if (sidebarToggle || closeSidebar) {

        // Add event listener for clicks on the toggle button
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault();
            sidebarWrapper.classList.toggle('toggled');
        });
        closeSidebar.addEventListener('click', event => {
            event.preventDefault();
            sidebarWrapper.classList.toggle('toggled');
        });
    }
}


document.addEventListener('DOMContentLoaded', function() {
    // Fetch and display the chat rooms list
    fetchChatRooms();
    toggleSidebarOnLoad();

    // Other initial setup tasks can go here
});


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
        anchor.appendChild(span);
        span.textContent = room.name;
        // If the room's ID/UUID matches the current URL, add the 'active-chatroom' class
        if(room.id === chatRoomIdOrUuid) {
            anchor.classList.add('active-chatroom');
        }
        listGroup.appendChild(anchor);
    });
}
