document.addEventListener("DOMContentLoaded", () => {
  const board = document.querySelector(".kb-board");
  if (!board) return;

  const csrfInput = document.querySelector(
    "#kb-csrf-form input[name='csrfmiddlewaretoken']",
  );

  const notice = document.querySelector("[data-kb-message]");

  let draggedCard = null;
  let saving = false;

  // Hiển thị thông báo thành công hoặc thất bại
  function showNotice(message, type) {
    if (!notice) return;

    notice.textContent = message;
    notice.dataset.type = type;
    notice.hidden = false;
  }

  // Cập nhật số lượng Task và trạng thái cột trống
  function refreshColumn(column) {
    const body = column.querySelector(".kb-column__body");
    const count = body.querySelectorAll(".kb-card").length;
    const counter = column.querySelector(".kb-column__count");

    if (counter) {
      counter.textContent = count;
    }

    let empty = body.querySelector(".kb-empty");

    if (!empty && count === 0) {
      empty = document.createElement("div");
      empty.className = "kb-empty";
      empty.textContent = "No tasks in this column";
      body.appendChild(empty);
    }

    if (empty) {
      empty.hidden = count !== 0;
    }
  }

  // Cập nhật cảnh báo quá hạn sau khi đổi trạng thái
  function refreshOverdue(card, isOverdue) {
    const dueDate = card.querySelector(".kb-due");

    if (dueDate) {
      dueDate.classList.toggle("kb-due--overdue", isOverdue);
    }

    const footer = card.querySelector(".kb-card__footer");
    if (!footer) return;

    let badge = footer.querySelector(".kb-overdue");

    if (isOverdue && !badge) {
      badge = document.createElement("span");
      badge.className = "kb-overdue";
      badge.textContent = "Overdue";
      footer.appendChild(badge);
    } else if (!isOverdue && badge) {
      badge.remove();
    }
  }

  // Xóa hiệu ứng highlight cột đích
  function clearDropTargets() {
    board.querySelectorAll(".kb-column--target").forEach((column) => {
      column.classList.remove("kb-column--target");
    });
  }

  // 1. Bắt đầu kéo Task
  board.addEventListener("dragstart", (event) => {
    const card = event.target.closest(".kb-card[draggable='true']");

    if (!card || saving || !event.dataTransfer) {
      event.preventDefault();
      return;
    }

    draggedCard = card;

    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", card.dataset.taskId || "");

    card.classList.add("kb-card--dragging");
  });

  // 2. Cho phép thả Task vào cột
  board.addEventListener("dragover", (event) => {
    if (!draggedCard || saving) return;

    const column = event.target.closest(".kb-column");
    if (!column) return;

    event.preventDefault();

    if (event.dataTransfer) {
      event.dataTransfer.dropEffect = "move";
    }

    clearDropTargets();

    if (column !== draggedCard.closest(".kb-column")) {
      column.classList.add("kb-column--target");
    }
  });

  // 3. Bỏ highlight khi kéo ra khỏi cột
  board.addEventListener("dragleave", (event) => {
    const column = event.target.closest(".kb-column");

    if (column && !column.contains(event.relatedTarget)) {
      column.classList.remove("kb-column--target");
    }
  });

  // 4. Xử lý khi thả Task
  board.addEventListener("drop", async (event) => {
    const targetColumn = event.target.closest(".kb-column");

    if (!draggedCard || saving || !targetColumn) return;

    event.preventDefault();

    const card = draggedCard;
    draggedCard = null;

    clearDropTargets();
    card.classList.remove("kb-card--dragging");

    const sourceColumn = card.closest(".kb-column");

    if (!sourceColumn || sourceColumn === targetColumn) {
      return;
    }

    // Lưu vị trí ban đầu để có thể hoàn tác
    const sourceBody = sourceColumn.querySelector(".kb-column__body");

    const nextSibling = card.nextSibling;

    const targetBody = targetColumn.querySelector(".kb-column__body");

    const newStatus = targetColumn.dataset.status;
    const requestUrl = card.dataset.moveUrl;

    if (!requestUrl || !newStatus || !csrfInput) {
      showNotice("Missing move URL or CSRF token.", "error");
      return;
    }

    saving = true;

    card.classList.add("kb-card--saving");
    card.setAttribute("aria-busy", "true");

    // Chuyển Task trên giao diện trước khi chờ server
    targetBody.appendChild(card);

    refreshColumn(sourceColumn);
    refreshColumn(targetColumn);

    try {
      // 5. Gửi POST đến Django
      const response = await fetch(requestUrl, {
        method: "POST",
        credentials: "same-origin",

        headers: {
          "X-CSRFToken": csrfInput.value,
          Accept: "application/json",
          "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        },

        body: new URLSearchParams({
          status: newStatus,
        }),
      });

      if (response.redirected) {
        throw new Error("Your session may have expired. Please log in again.");
      }

      const contentType = response.headers.get("content-type") || "";

      if (!contentType.includes("application/json")) {
        throw new Error("Unexpected server response.");
      }

      // 6. Nhận kết quả từ Django
      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || `HTTP ${response.status}`);
      }

      if (data.status !== newStatus) {
        throw new Error("Server returned a different task status.");
      }

      // 7. Cập nhật giao diện sau khi lưu thành công
      refreshOverdue(card, Boolean(data.is_overdue));

      const columnTitle =
        targetColumn.querySelector("h2")?.textContent || newStatus;

      showNotice(
        `Task #${card.dataset.taskId} moved to ${columnTitle}.`,
        "success",
      );
    } catch (error) {
      // 8. Nếu lỗi, trả Task về cột ban đầu
      sourceBody.insertBefore(card, nextSibling);

      refreshColumn(sourceColumn);
      refreshColumn(targetColumn);

      showNotice(`Could not save this change: ${error.message}`, "error");
    } finally {
      saving = false;

      card.classList.remove("kb-card--saving");
      card.removeAttribute("aria-busy");
    }
  });

  // 9. Dọn dẹp khi kết thúc thao tác kéo
  board.addEventListener("dragend", () => {
    if (draggedCard) {
      draggedCard.classList.remove("kb-card--dragging");
    }

    draggedCard = null;
    clearDropTargets();
  });

  // Khởi tạo số lượng Task trên từng cột
  board.querySelectorAll(".kb-column").forEach(refreshColumn);
});
