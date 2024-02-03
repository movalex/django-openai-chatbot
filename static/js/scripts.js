
window.addEventListener('DOMContentLoaded', event => {
    // Get the button 
    const sidebarToggle = document.body.querySelector('#sidebarToggle');
    const closeSidebar = document.body.querySelector('#closeButton');
    
    if (sidebarToggle || closeSidebar) {
        const sidebarWrapper = document.getElementById('sidebar-wrapper');

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
