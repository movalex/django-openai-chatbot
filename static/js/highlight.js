function loadHighlightJs() {
    var script = document.createElement('script');
    script.src = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.3.1/highlight.min.js";
    script.onload = function () {
        hljs.highlightAll() // Initialize Highlight.js when the script is loaded
    };
    document.head.appendChild(script);
}
// Call the function when the window loads
window.onload = loadHighlightJs;