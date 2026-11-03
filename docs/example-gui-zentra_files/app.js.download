const enterFullPage = document.querySelector("[data-enter-full-page]");
const exitFullPage = document.querySelector("[data-exit-full-page]");

const updateFullPageUrl = (enabled) => {
  const url = new URL(window.location.href);
  if (enabled) url.searchParams.set("full_page", "1");
  else url.searchParams.delete("full_page");
  window.history.replaceState(window.history.state, "", url);
};

const setFullPageMode = (enabled) => {
  document.body.classList.toggle("full-page-mode", enabled);
  enterFullPage?.setAttribute("aria-pressed", String(enabled));
  updateFullPageUrl(enabled);
  if (enabled) exitFullPage?.focus();
  else enterFullPage?.focus();
};

enterFullPage?.addEventListener("click", () => setFullPageMode(true));
exitFullPage?.addEventListener("click", () => setFullPageMode(false));

document.addEventListener("submit", (event) => {
  if (!document.body.classList.contains("full-page-mode")) return;
  const form = event.target;
  if (!(form instanceof HTMLFormElement) || form.method.toLowerCase() !== "get") return;
  let state = form.querySelector('input[name="full_page"]');
  if (!state) {
    state = document.createElement("input");
    state.type = "hidden";
    state.name = "full_page";
    form.append(state);
  }
  state.value = "1";
});

document.addEventListener("click", (event) => {
  if (!document.body.classList.contains("full-page-mode")) return;
  const link = event.target.closest("a[href]");
  if (!link || link.target === "_blank") return;
  const url = new URL(link.href, window.location.href);
  if (url.origin !== window.location.origin) return;
  url.searchParams.set("full_page", "1");
  link.href = url.href;
});
