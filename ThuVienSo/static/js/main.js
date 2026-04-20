document.addEventListener("DOMContentLoaded", function () {
    const navLinks = document.querySelectorAll(".navbar-links a");
    const currentPath = window.location.pathname;

    navLinks.forEach(function (link) {
        if (link.getAttribute("href") === currentPath) {
            link.style.color = "#fff";
            link.style.fontWeight = "700";
        }
    });
});
