
window.addEventListener('DOMContentLoaded', event => {
    // Get the button 
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    const closeSidebar = document.body.querySelector('#topRightButton');
    
    if (sidebarToggle || closeSidebar) {
        const sidebarWrapper = document.getElementById('sidebar-wrapper');

        // Add event listener for clicks on the toggle button
        sidebarToggle.addEventListener('click', event => {
            event.preventDefault();
            sidebarWrapper.classList.toggle('toggled'); // Ensure this matches the class used in CSS
        });
        closeSidebar.addEventListener('click', event => {
            event.preventDefault();
            sidebarWrapper.classList.toggle('toggled'); // Ensure this matches the class used in CSS
        });
    }
});


function checkScroll() {
    const scrollContainer = document.querySelector(".main-chat-body");
    const scrollToBottomBtn = document.getElementById("scrollToBottomBtn");
    const chatList = document.querySelector(".chat-container");
    
    // Check if the container is scrolled to the bottom

    const offset = 5; // Adjust this offset as needed
    if (scrollContainer.scrollHeight - scrollContainer.scrollTop <= scrollContainer.clientHeight + offset) {
        // Hide the button if scrolled to the bottom
        scrollToBottomBtn.style.display = 'none';
    } else {
        // Show the button if not scrolled to the bottom
        scrollToBottomBtn.style.display = 'block';
    }
    // Show or hide the button based on the chat list content
    if (chatList.clientHeight === 0 || scrollContainer.scrollHeight <= scrollContainer.clientHeight) {
        scrollToBottomBtn.style.display = 'none'; // Hide the scroll button if the chat list is empty or if there's no scrollbar
    }

}
// Event listener for scrolling in the container
document.querySelector(".main-chat-body").addEventListener('scroll', checkScroll);

function adjustButtonPadding() {
    const mainContainer = document.querySelector('.main-chat-body'); // Replace with your main container's selector
    const scrollToBottomBtn = document.getElementById('scrollToBottomBtn');

    if (mainContainer && scrollToBottomBtn) {
        const containerRect = mainContainer.getBoundingClientRect();
        const windowHeight = window.innerHeight;
        const bottomPadding = windowHeight - containerRect.bottom;
        scrollToBottomBtn.style.bottom = `${bottomPadding+5}px`;
    }
}

// Adjust the height on load and when the window is resized
window.addEventListener('load', adjustButtonPadding);
window.addEventListener('resize', adjustButtonPadding);


