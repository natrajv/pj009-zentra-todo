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

const taskTitle = document.getElementById("new-task-title");
if (taskTitle) taskTitle.focus();

const editTitle = document.getElementById("edit-task-title");
if (editTitle && !document.getElementById("task-edit-form").hidden) editTitle.focus();
