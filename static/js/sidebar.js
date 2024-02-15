const sidebarWrapper = document.getElementById('sidebar-wrapper');

window.addEventListener('DOMContentLoaded', event => {
    // Get the button 
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    const closeSidebar = document.body.querySelector('#closeButton');
    
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
});

// Add click event listener to the document
document.addEventListener('click', (event) => {

    // Check if the click is on the toggle button or its children
    if (sidebarToggle.contains(event.target)) {
        event.preventDefault(); // Only call this if the click is on the toggle button
        return;
    }
    // Check if the click is on the toggle button or its children
    if (!sidebarWrapper || sidebarToggle.contains(event.target)) {
        return;
    }
    // Check if the click is outside the sidebar
    if (sidebarWrapper && !sidebarWrapper.contains(event.target)) {
        // Close the sidebar
        sidebarWrapper.classList.remove('toggled');
    }
});
    

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
