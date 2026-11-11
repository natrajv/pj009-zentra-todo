const pageDialog = document.querySelector("dialog[data-page-dialog]");
const openModal = (dialog) => {
  if (dialog) dialog.showModal();
};
if (pageDialog) {
  openModal(pageDialog);

  const closeLink = pageDialog.querySelector(".dialog-header a[href]");
  pageDialog.addEventListener("close", () => {
    if (closeLink) window.history.replaceState(window.history.state, "", closeLink.href);
  });
}
const editTitle = document.getElementById("edit-task-title");
if (editTitle) editTitle.focus();

const confirmDialog = document.querySelector("dialog[data-confirm-dialog]");
const openConfirm = document.querySelector("[data-open-confirm]");
openConfirm?.addEventListener("click", () => openModal(confirmDialog));

document.querySelectorAll("table[data-grid]").forEach((table) => {
  const grid = table.dataset.grid;
  const columns = [...table.querySelectorAll("col[data-col]")];
  const saveTimers = new WeakMap();
  const status = document.createElement("span");
  status.className = "sr-only";
  status.setAttribute("role", "status");
  table.parentElement.insertAdjacentElement("afterend", status);
  table.querySelectorAll("thead th .resize-handle").forEach((handle, index) => {
    const column = columns[index];
    if (!column) return;
    handle.tabIndex = 0;
    handle.setAttribute("role", "separator");
    handle.setAttribute("aria-orientation", "vertical");
    handle.setAttribute("aria-label", `Resize ${column.dataset.col} column`);
    handle.setAttribute("aria-valuemin", "60");
    handle.setAttribute("aria-valuemax", "800");
    handle.setAttribute("aria-valuenow", String(Math.round(column.getBoundingClientRect().width)));
    const save = async (width) => {
      const form = new FormData();
      form.set("column", column.dataset.col);
      form.set("width", String(width));
      form.set("csrf_token", document.querySelector('meta[name="csrf-token"]')?.content || "");
      try {
        const response = await fetch(`/preferences/grid-widths/${grid}`, { method: "POST", body: form, credentials: "same-origin" });
        if (!response.ok) throw new Error("Preference save failed");
        status.textContent = "Column width saved.";
      } catch {
        status.textContent = "Column width could not be saved. It will return to its previous setting after reloading.";
      }
    };
    const scheduleSave = (width) => {
      window.clearTimeout(saveTimers.get(handle));
      saveTimers.set(handle, window.setTimeout(() => save(width), 300));
    };
    handle.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
      event.preventDefault();
      const width = Math.max(60, Math.min(800, Math.round(column.getBoundingClientRect().width + (event.key === "ArrowRight" ? 10 : -10))));
      column.style.width = `${width}px`;
      handle.setAttribute("aria-valuenow", String(width));
      scheduleSave(width);
    });
    handle.addEventListener("pointerdown", (event) => {
      event.preventDefault();
      handle.setPointerCapture(event.pointerId);
      const startX = event.clientX;
      const startWidth = column.getBoundingClientRect().width;
      const move = (moveEvent) => {
        const width = Math.max(60, Math.min(800, Math.round(startWidth + moveEvent.clientX - startX)));
        column.style.width = `${width}px`;
        handle.dataset.width = String(width);
        handle.setAttribute("aria-valuenow", String(width));
      };
      const finish = () => {
        handle.removeEventListener("pointermove", move);
        handle.removeEventListener("pointerup", finish);
        handle.removeEventListener("pointercancel", finish);
        if (handle.dataset.width) scheduleSave(Number(handle.dataset.width));
      };
      handle.addEventListener("pointermove", move);
      handle.addEventListener("pointerup", finish);
      handle.addEventListener("pointercancel", finish);
    });
  });
});
