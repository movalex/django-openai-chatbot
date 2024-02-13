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
        // Add your logic to handle sidebar toggle here
        // For example, toggling a class to show/hide the sidebar
        return; // Exit the function to avoid further logic execution
    }
    // Check if the click is on the toggle button or its children
    if (!sidebarWrapper || sidebarToggle.contains(event.target)) {
        return; // Do nothing if the click is on the toggle button
    }
    // Check if the click is outside the sidebar
    if (sidebarWrapper && !sidebarWrapper.contains(event.target)) {
        // Close the sidebar
        sidebarWrapper.classList.remove('toggled');
    }
});
    
