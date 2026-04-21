document.addEventListener("DOMContentLoaded", function () {
    const input = document.querySelector(".search-input");
    if (input) {
        input.focus();
        const len = input.value.length;
        input.setSelectionRange(len, len);
    }
});
