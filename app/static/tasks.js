document.querySelectorAll("[data-task-row]").forEach((row) => {
  row.addEventListener("click", (event) => {
    if (event.target.closest("button, input, select, form")) return;
    if (event.ctrlKey) {
      event.preventDefault();
      window.location.assign(row.dataset.editUrl);
    } else if (!event.target.closest("a")) {
      window.location.assign(row.dataset.viewUrl);
    }
  });
});

document.querySelectorAll("[data-search-row]").forEach((row) => {
  const open = (event) => {
    if (event.target.closest("a, button, input, select")) return;
    if (event.type === "keydown" && !["Enter", " "].includes(event.key)) return;
    event.preventDefault();
    window.location.assign(row.dataset.viewUrl);
  };
  row.addEventListener("click", open);
  row.addEventListener("keydown", open);
});

const taskTitle = document.getElementById("new-task-title");
if (taskTitle) taskTitle.focus();

const editTitle = document.getElementById("edit-task-title");
if (editTitle && !document.getElementById("task-edit-form").hidden) editTitle.focus();

document.querySelectorAll("table[data-grid]").forEach((table) => {
  const grid = table.dataset.grid;
  const columns = [...table.querySelectorAll("col[data-col]")];
  table.querySelectorAll("thead th .resize-handle").forEach((handle, index) => {
    const column = columns[index];
    if (!column) return;
    handle.tabIndex = 0;
    handle.setAttribute("role", "separator");
    handle.setAttribute("aria-label", `Resize ${column.dataset.col} column`);
    const save = async (width) => {
      const form = new FormData();
      form.set("column", column.dataset.col);
      form.set("width", String(width));
      form.set("csrf_token", document.querySelector('meta[name="csrf-token"]')?.content || "");
      await fetch(`/preferences/grid-widths/${grid}`, { method: "POST", body: form, credentials: "same-origin" });
    };
    handle.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
      event.preventDefault();
      const width = Math.max(60, Math.min(800, Math.round(column.getBoundingClientRect().width + (event.key === "ArrowRight" ? 10 : -10))));
      column.style.width = `${width}px`;
      save(width);
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
      };
      const finish = () => {
        handle.removeEventListener("pointermove", move);
        handle.removeEventListener("pointerup", finish);
        handle.removeEventListener("pointercancel", finish);
        if (handle.dataset.width) save(Number(handle.dataset.width));
      };
      handle.addEventListener("pointermove", move);
      handle.addEventListener("pointerup", finish);
      handle.addEventListener("pointercancel", finish);
    });
  });
});
