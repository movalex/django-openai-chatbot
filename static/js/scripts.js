/*!
* Start Bootstrap - Simple Sidebar v6.0.6 (https://startbootstrap.com/template/simple-sidebar)
* Copyright 2013-2023 Start Bootstrap
* Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-simple-sidebar/blob/master/LICENSE)
*/
// 
// Scripts
// 


// console.log("you have to work")

// window.addEventListener('DOMContentLoaded', event => {

//     // Toggle the side navigation
//     const sidebarToggle = document.body.querySelector('#sidebarToggle');
//     if (sidebarToggle) {
//         // Uncomment Below to persist sidebar toggle between refreshes
//         // if (localStorage.getItem('sb|sidebar-toggle') === 'true') {
//         //     document.body.classList.toggle('sb-sidenav-toggled');
//         // }
//         sidebarToggle.addEventListener('click', event => {
//             event.preventDefault();
//             document.body.classList.toggle('sb-sidenav-toggled');
//             localStorage.setItem('sb|sidebar-toggle', document.body.classList.contains('sb-sidenav-toggled'));
//         });
//     }
// });
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
    if (scrollContainer.scrollHeight - scrollContainer.scrollTop === scrollContainer.clientHeight) {
        // Hide the button if scrolled to the bottom
        scrollToBottomBtn.style.display = 'none';
    } else {
        // Show the button if not scrolled to the bottom
        scrollToBottomBtn.style.display = 'block';
    }
}

// Event listener for scrolling in the container
document.querySelector(".container-fluid-custom").addEventListener('scroll', checkScroll);
