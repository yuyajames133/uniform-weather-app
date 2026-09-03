(() => {
  const genderButtons = [...document.querySelectorAll(".gender-btn")];
  const cards = [...document.querySelectorAll(".outfit-card")];
  const mainPanel = document.getElementById("coordinateView");
  const genderTitle = document.getElementById("genderTitle");
  const genderEyebrow = document.getElementById("genderEyebrow");
  const tipLabel = document.getElementById("tipLabel");

  function refreshIcons() {
    if (window.lucide) window.lucide.createIcons();
  }

  function setGender(gender) {
    genderButtons.forEach(btn => btn.classList.toggle("active", btn.dataset.gender === gender));
    cards.forEach(card => card.classList.toggle("show-gender", card.dataset.gender === gender));

    const girls = gender === "girls";
    mainPanel.classList.toggle("girls-mode", girls);
    genderTitle.textContent = girls ? "女子のおすすめコーデ" : "男子のおすすめコーデ";
    genderEyebrow.textContent = girls ? "GIRLS" : "BOYS";
    tipLabel.textContent = girls ? "女子のポイント" : "男子のポイント";

    const track = document.querySelector(".outfit-track");
    track.scrollLeft = 0;
  }

  genderButtons.forEach(btn => btn.addEventListener("click", () => setGender(btn.dataset.gender)));

  const viewTabs = [...document.querySelectorAll(".view-tab")];
  const views = {
    coordinate: document.getElementById("coordinateView"),
    forecast: document.getElementById("forecastView"),
    advice: document.getElementById("adviceView")
  };

  viewTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      viewTabs.forEach(t => t.classList.toggle("active", t === tab));
      Object.entries(views).forEach(([name, panel]) => {
        panel.hidden = name !== tab.dataset.view;
      });
    });
  });

  function getSaved() {
    try { return JSON.parse(localStorage.getItem("uniformFavorites") || "[]"); }
    catch { return []; }
  }

  function setSaved(ids) {
    localStorage.setItem("uniformFavorites", JSON.stringify(ids));
  }

  function syncHearts() {
    const saved = getSaved();
    document.querySelectorAll(".js-heart").forEach(btn => {
      btn.classList.toggle("saved", saved.includes(btn.dataset.id));
    });
  }

  document.querySelectorAll(".js-heart").forEach(btn => {
    btn.addEventListener("click", event => {
      event.stopPropagation();
      const id = btn.dataset.id;
      const saved = getSaved();
      setSaved(saved.includes(id) ? saved.filter(x => x !== id) : [...saved, id]);
      syncHearts();
    });
  });

  document.getElementById("favoriteTop")?.addEventListener("click", () => {
    const firstSaved = document.querySelector(".js-heart.saved");
    if (firstSaved) firstSaved.scrollIntoView({behavior:"smooth", inline:"center", block:"nearest"});
  });

  setGender("boys");
  syncHearts();
  refreshIcons();
})();
