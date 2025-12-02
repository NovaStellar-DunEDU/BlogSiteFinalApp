document.addEventListener("DOMContentLoaded", function () {
    const textareas = document.querySelectorAll(".growtextarea");

    textareas.forEach(textarea => {
        function resize() {
            textarea.style.height = "auto"; // reset
            textarea.style.height = textarea.scrollHeight + "px"; // fit content
        }

        textarea.addEventListener("input", resize);
        window.addEventListener("resize", resize);

        resize(); // initialize
    });
});
