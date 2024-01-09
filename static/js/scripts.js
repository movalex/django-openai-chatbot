
window.addEventListener('DOMContentLoaded', event => {
    // Get the button 
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    
    if (sidebarToggle) {
        const sidebarWrapper = document.getElementById('sidebar-wrapper');

        // Add event listener for clicks on the toggle button
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault();
            sidebarWrapper.classList.toggle('toggled'); // Ensure this matches the class used in CSS
        });
    }
});

// function adjustChatListHeight() {
//     var sidebarWrapper = document.getElementById('sidebar-wrapper');
//     var headerHeight = sidebarWrapper.querySelector('.mb-3').offsetHeight; // Assuming this is the header
//     var footerHeight = sidebarWrapper.querySelector('.footer').offsetHeight;
//     var viewportHeight = window.innerHeight;

//     var chatListHeight = viewportHeight - headerHeight - footerHeight;
//     sidebarWrapper.querySelector('.scrollarea').style.maxHeight = chatListHeight + 'px';
// }

// // Run on load and resize
// window.onload = adjustChatListHeight;
// window.onresize = adjustChatListHeight;

function checkScroll() {
    const scrollContainer = document.querySelector(".container-fluid-custom");
    const scrollToBottomBtn = document.getElementById("scrollToBottomBtn");
    
    // Check if the container is scrolled to the bottom

    const offset = 5; // Adjust this offset as needed
    if (scrollContainer.scrollHeight - scrollContainer.scrollTop <= scrollContainer.clientHeight + offset) {
        // Hide the button if scrolled to the bottom
        scrollToBottomBtn.style.display = 'none';
    } else {
        // Show the button if not scrolled to the bottom
        scrollToBottomBtn.style.display = 'block';
    }
}
// Event listener for scrolling in the container
document.querySelector(".container-fluid-custom").addEventListener('scroll', checkScroll);

function adjustChatContainerHeight() {
    const footerHeight = document.querySelector('.chat-footer').offsetHeight;
    const chatContainer = document.querySelector('.container-fluid-custom');
    const viewportHeight = window.innerHeight;

    chatContainer.style.height = `${viewportHeight - footerHeight}px`;
}

// Adjust the height on load and when the window is resized
window.addEventListener('load', adjustChatContainerHeight);
window.addEventListener('resize', adjustChatContainerHeight);


