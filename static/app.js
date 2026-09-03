(() => {
  const buttons = [...document.querySelectorAll(".gender")];
  const grids = [...document.querySelectorAll("[data-grid]")];
  buttons.forEach(button => {
    button.addEventListener("click", () => {
      buttons.forEach(b => b.classList.toggle("active", b === button));
      grids.forEach(grid => grid.classList.toggle("active", grid.dataset.grid === button.dataset.gender));
    });
  });

  document.querySelectorAll(".heart").forEach(btn => {
    btn.addEventListener("click", () => {
      btn.classList.toggle("saved");
      btn.style.color = btn.classList.contains("saved") ? "#d76b82" : "#8a95a5";
      const svg = btn.querySelector("svg");
      if (svg) svg.style.fill = btn.classList.contains("saved") ? "currentColor" : "none";
    });
  });

  if (window.lucide) window.lucide.createIcons();
  else window.addEventListener("load", () => window.lucide?.createIcons(), {once:true});
})();
