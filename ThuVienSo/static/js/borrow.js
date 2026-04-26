document.addEventListener("DOMContentLoaded", function () {
    const modal = document.getElementById("deleteBorrowModal");
    const cancelBtn = document.getElementById("cancelDeleteBorrow");
    const confirmBtn = document.getElementById("confirmDeleteBorrow");
    const message = document.getElementById("deleteBorrowMessage");

    let selectedForm = null;

    const deleteButtons = document.querySelectorAll(".js-open-delete-modal");

    deleteButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            selectedForm = button.closest("form");

            const bookTitle = button.dataset.bookTitle || "yêu cầu này";

            message.textContent = `Bạn có chắc muốn xóa yêu cầu mượn sách "${bookTitle}" không?`;

            modal.classList.add("show");
        });
    });

    cancelBtn.addEventListener("click", function () {
        modal.classList.remove("show");
        selectedForm = null;
    });

    confirmBtn.addEventListener("click", function () {
        if (selectedForm) {
            selectedForm.submit();
        }
    });

    modal.addEventListener("click", function (event) {
        if (event.target === modal) {
            modal.classList.remove("show");
            selectedForm = null;
        }
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            modal.classList.remove("show");
            selectedForm = null;
        }
    });
});