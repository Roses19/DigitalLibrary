document.addEventListener("DOMContentLoaded", function () {
    const rejectModal = document.getElementById("rejectBorrowModal");
    const rejectForm = document.getElementById("rejectBorrowForm");
    const rejectReason = document.getElementById("rejectReason");
    const rejectNextUrl = document.getElementById("rejectNextUrl");
    const cancelRejectBtn = document.getElementById("cancelRejectBorrow");
    const rejectMessage = document.getElementById("rejectBorrowMessage");

    if (!rejectModal || !rejectForm || !rejectReason || !cancelRejectBtn) {
        return;
    }

    const rejectButtons = document.querySelectorAll(".js-open-reject-modal");

    rejectButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            const action = button.dataset.action;
            const requestId = button.dataset.requestId;
            const nextUrl = button.dataset.nextUrl || "/admin?tab=borrow";

            rejectForm.action = action;
            rejectReason.value = "";

            if (rejectNextUrl) {
                rejectNextUrl.value = nextUrl;
            }

            if (rejectMessage) {
                rejectMessage.textContent = `Nhập lý do từ chối yêu cầu mượn #${requestId}.`;
            }

            rejectModal.classList.add("show");

            setTimeout(function () {
                rejectReason.focus();
            }, 100);
        });
    });

    function closeModal() {
        rejectModal.classList.remove("show");
        rejectForm.action = "";
        rejectReason.value = "";

        if (rejectNextUrl) {
            rejectNextUrl.value = "/admin?tab=borrow";
        }
    }

    cancelRejectBtn.addEventListener("click", closeModal);

    rejectModal.addEventListener("click", function (event) {
        if (event.target === rejectModal) {
            closeModal();
        }
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeModal();
        }
    });
});