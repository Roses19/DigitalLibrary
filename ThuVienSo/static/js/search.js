
document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("searchFilterForm");
    const keywordInput = document.querySelector(".sidebar-search-input");

    if (!form || !keywordInput) {
        return;
    }

    const resetUrl = form.dataset.resetUrl || form.action;

    // Mở / đóng nhóm filter
    const toggles = document.querySelectorAll(".filter-toggle");

    toggles.forEach(function (toggle) {
        toggle.addEventListener("click", function () {
            const group = toggle.closest(".filter-group");

            if (group) {
                group.classList.toggle("open");
            }
        });
    });

    // Xử lý submit form
    form.addEventListener("submit", function (event) {
        const submitter = event.submitter;
        const keyword = keywordInput.value.trim();

        const isApplyFilterButton =
            submitter && submitter.classList.contains("apply-filter-btn");

        /*
            Nếu bấm nút tìm kiếm hoặc nhấn Enter trong ô tìm kiếm:
            - Không giữ lại checkbox cũ
            - Chỉ gửi keyword mới
        */
        if (!isApplyFilterButton) {
            // Nếu keyword rỗng thì reset toàn bộ trang search
            if (keyword === "") {
                event.preventDefault();
                window.location.href = resetUrl;
                return;
            }

            // Nếu có keyword mới thì bỏ các filter cũ khỏi request
            const filterInputs = form.querySelectorAll(
                "input[name='category'], input[name='publisher'], input[name='status']"
            );

            filterInputs.forEach(function (input) {
                input.disabled = true;
            });
        }
    });
});