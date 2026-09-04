(() => {
  const buttons = [...document.querySelectorAll(".gender")];
  const panels = [...document.querySelectorAll("[data-panel]")];

  buttons.forEach(button => {
    button.addEventListener("click", () => {
      const gender = button.dataset.gender;

      buttons.forEach(btn => {
        btn.classList.toggle("active", btn === button);
      });

      panels.forEach(panel => {
        panel.classList.toggle("active", panel.dataset.panel === gender);
      });
    });
  });

  if (window.lucide) {
    window.lucide.createIcons();
  } else {
    window.addEventListener(
      "load",
      () => window.lucide?.createIcons(),
      { once:true }
    );
  }
})();
