(() => {
  const appData = window.APP_DATA || {};
  const tabs = [...document.querySelectorAll(".js-tab")];
  const panels = [...document.querySelectorAll("[data-panel]")];
  const cards = [...document.querySelectorAll(".outfit-card")];
  const favoriteButtons = [...document.querySelectorAll(".js-favorite")];
  const favoritesGrid = document.getElementById("favoritesGrid");
  const favoritesEmpty = document.getElementById("favoritesEmpty");
  const dialog = document.getElementById("outfitDialog");
  const dialogClose = document.getElementById("dialogClose");
  const dialogImage = document.getElementById("dialogImage");
  const dialogTemp = document.getElementById("dialogTemp");
  const dialogTitle = document.getElementById("dialogTitle");
  const dialogDescription = document.getElementById("dialogDescription");
  const dialogTags = document.getElementById("dialogTags");
  const dialogFavorite = document.getElementById("dialogFavorite");

  const allItems = [...(appData.outfits?.girls || []), ...(appData.outfits?.boys || [])];
  let activeDialogId = null;
  let chartInstance = null;

  function refreshIcons() {
    if (window.lucide) window.lucide.createIcons();
  }

  function getSaved() {
    try { return JSON.parse(localStorage.getItem("uniformFavorites") || "[]"); }
    catch { return []; }
  }

  function setSaved(ids) {
    localStorage.setItem("uniformFavorites", JSON.stringify(ids));
  }

  function toggleFavorite(id) {
    const saved = getSaved();
    const next = saved.includes(id) ? saved.filter(v => v !== id) : [...saved, id];
    setSaved(next);
    syncFavorites();
    renderFavorites();
  }

  function syncFavorites() {
    const saved = getSaved();
    favoriteButtons.forEach(button => {
      const on = saved.includes(button.dataset.id);
      button.classList.toggle("saved", on);
      button.setAttribute("aria-label", on ? "お気に入りから削除" : "お気に入りに追加");
    });
    if (activeDialogId) {
      const on = saved.includes(activeDialogId);
      dialogFavorite.innerHTML = on
        ? '<i data-lucide="heart"></i> お気に入りから削除'
        : '<i data-lucide="heart"></i> お気に入りに追加';
      refreshIcons();
    }
  }

  function renderFavorites() {
    if (!favoritesGrid || !favoritesEmpty) return;
    const saved = getSaved();
    const rows = allItems.filter(item => saved.includes(item.id));
    favoritesGrid.innerHTML = "";
    favoritesEmpty.hidden = rows.length > 0;

    rows.forEach(item => {
      const card = document.createElement("article");
      card.className = "favorite-card";
      card.innerHTML = `
        <img src="/static/images/${item.image}" alt="${item.title}">
        <div>
          <h3>${item.title}</h3>
          <p>${item.description}</p>
          <div class="tags">${item.tags.map(tag => `<span>${tag}</span>`).join("")}</div>
        </div>`;
      favoritesGrid.appendChild(card);
    });
  }

  function showTab(name) {
    document.querySelectorAll(".tab").forEach(tab => tab.classList.toggle("active", tab.dataset.tab === name));
    panels.forEach(panel => panel.classList.toggle("active", panel.dataset.panel === name));
    if (name === "graph") initChart();
    if (name === "favorites") renderFavorites();
  }

  tabs.forEach(tab => tab.addEventListener("click", () => showTab(tab.dataset.tab)));

  favoriteButtons.forEach(button => {
    button.addEventListener("click", event => {
      event.stopPropagation();
      toggleFavorite(button.dataset.id);
    });
  });

  function openCard(card) {
    activeDialogId = card.dataset.id;
    dialogImage.src = card.dataset.image;
    dialogImage.alt = card.dataset.title;
    dialogTemp.textContent = `おすすめ気温 ${card.dataset.temp}`;
    dialogTitle.textContent = card.dataset.title;
    dialogDescription.textContent = card.dataset.description;
    dialogTags.innerHTML = card.dataset.tags.split("・").map(tag => `<span>${tag}</span>`).join("");
    syncFavorites();
    dialog.showModal();
  }

  cards.forEach(card => {
    card.addEventListener("click", () => openCard(card));
    card.addEventListener("keydown", event => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        openCard(card);
      }
    });
  });

  dialogClose?.addEventListener("click", () => dialog.close());
  dialog?.addEventListener("click", event => { if (event.target === dialog) dialog.close(); });
  dialogFavorite?.addEventListener("click", () => { if (activeDialogId) toggleFavorite(activeDialogId); });
  document.getElementById("refreshWeather")?.addEventListener("click", () => window.location.reload());

  document.getElementById("saveRecommended")?.addEventListener("click", () => {
    const saved = new Set(getSaved());
    allItems.filter(item => item.recommended).forEach(item => saved.add(item.id));
    setSaved([...saved]);
    syncFavorites();
    renderFavorites();

    const button = document.getElementById("saveRecommended");
    button.innerHTML = '<i data-lucide="check"></i> 保存しました';
    refreshIcons();
    window.setTimeout(() => {
      button.innerHTML = '<i data-lucide="bookmark"></i>今日のBESTを保存';
      refreshIcons();
    }, 1400);
  });

  function initChart() {
    if (chartInstance || !window.Chart) return;
    const canvas = document.getElementById("weatherChart");
    if (!canvas) return;

    chartInstance = new Chart(canvas, {
      type: "line",
      data: {
        labels: appData.chart?.labels || [],
        datasets: [
          {
            label: "気温 (°C)",
            data: appData.chart?.temps || [],
            borderColor: "#315f96",
            backgroundColor: "rgba(49,95,150,.08)",
            tension: .35,
            fill: true,
            yAxisID: "temp",
            pointRadius: 3
          },
          {
            label: "降水確率 (%)",
            data: appData.chart?.rain || [],
            borderColor: "#72a9d8",
            backgroundColor: "rgba(114,169,216,.08)",
            tension: .35,
            yAxisID: "rain",
            pointRadius: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: {
            labels: { usePointStyle: true, boxWidth: 8, font: { size: 11 } }
          }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: "#758196", font: { size: 10 } }
          },
          temp: {
            position: "left",
            grid: { color: "rgba(111,124,144,.10)" },
            ticks: { color: "#758196", font: { size: 10 } }
          },
          rain: {
            position: "right",
            min: 0,
            max: 100,
            grid: { drawOnChartArea: false },
            ticks: {
              color: "#758196",
              font: { size: 10 },
              callback: value => `${value}%`
            }
          }
        }
      }
    });
  }

  syncFavorites();
  renderFavorites();
  refreshIcons();
})();
