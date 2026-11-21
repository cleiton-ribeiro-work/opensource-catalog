(() => {
  "use strict";

  const data = window.CATALOG_DATA;
  if (!data || !Array.isArray(data.categories)) {
    console.error("CATALOG_DATA não encontrado. Verifique se data.js foi carregado.");
    return;
  }

  const CATEGORY_COLORS = {
    aiml: "#8b5cf6",
    automation: "#f59e0b",
    developerTools: "#3b82f6",
    infrastructure: "#06b6d4",
    databases: "#ec4899",
    observability: "#14b8a6",
    security: "#ef4444",
    analytics: "#6366f1",
    cms: "#84cc16",
    eCommerce: "#f97316",
    communication: "#0ea5e9",
    productivity: "#10b981",
    storageFiles: "#a855f7",
    media: "#e11d48",
    finance: "#22c55e",
    homeLifestyle: "#eab308",
    utilities: "#64748b",
    other: "#94a3b8",
  };

  const state = {
    query: "",
    category: "all",
    rec: "all",
    sort: "score-desc",
    filters: { popular: false, git: false, demo: false, stars10k: false, activeOnly: false },
    view: "grouped",
  };

  const allServices = data.categories.flatMap((c) => c.services);
  const serviceById = new Map(allServices.map((s) => [s.id, s]));

  const el = {
    html: document.documentElement,
    headerCountBadge: document.getElementById("headerCountBadge"),
    searchInput: document.getElementById("searchInput"),
    clearSearchBtn: document.getElementById("clearSearchBtn"),
    sortSelect: document.getElementById("sortSelect"),
    viewButtons: document.querySelectorAll(".view-btn"),
    filterChips: document.querySelectorAll(".filter-chip[data-filter]"),
    recChips: document.querySelectorAll(".rec-chip[data-rec]"),
    categoryNav: document.getElementById("categoryNav"),
    catalogContainer: document.getElementById("catalogContainer"),
    emptyState: document.getElementById("emptyState"),
    activeHeading: document.getElementById("activeHeading"),
    resultsCounter: document.getElementById("resultsCounter"),
    resetFiltersBtn: document.getElementById("resetFiltersBtn"),
    emptyResetBtn: document.getElementById("emptyResetBtn"),
    statLeader: document.getElementById("statLeader"),
    statRecommended: document.getElementById("statRecommended"),
    statNiche: document.getElementById("statNiche"),
    statCaution: document.getElementById("statCaution"),
    statActive: document.getElementById("statActive"),
    statStars10k: document.getElementById("statStars10k"),
    statPopular: document.getElementById("statPopular"),
    statGit: document.getElementById("statGit"),
    statDemo: document.getElementById("statDemo"),
    statTotal: document.getElementById("statTotal"),
    statCats: document.getElementById("statCats"),
    statOfficial: document.getElementById("statOfficial"),
    footerStats: document.getElementById("footerStats"),
    themeToggleBtn: document.getElementById("themeToggleBtn"),
    mobileMenuBtn: document.getElementById("mobileMenuBtn"),
    sidebar: document.getElementById("sidebar"),
    sidebarBackdrop: document.getElementById("sidebarBackdrop"),
    exportToggleBtn: document.getElementById("exportToggleBtn"),
    exportMenu: document.getElementById("exportMenu"),
    backToTopBtn: document.getElementById("backToTopBtn"),
    modal: document.getElementById("serviceModal"),
    modalCloseBtn: document.getElementById("modalCloseBtn"),
    modalIconWrap: document.getElementById("modalIconWrap"),
    modalCategory: document.getElementById("modalCategory"),
    modalTitle: document.getElementById("modalTitle"),
    modalDesc: document.getElementById("modalDesc"),
    modalScoreCard: document.getElementById("modalScoreCard"),
    modalFeaturesWrap: document.getElementById("modalFeaturesWrap"),
    modalFeaturesList: document.getElementById("modalFeaturesList"),
    modalLinks: document.getElementById("modalLinks"),
  };

  function escapeHtml(str) {
    return String(str ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function initials(name) {
    const parts = String(name).trim().split(/[\s\-_/]+/).filter(Boolean);
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return String(name).slice(0, 2).toUpperCase();
  }

  function formatCompact(n) {
    if (n === null || n === undefined) return "—";
    if (n >= 1000000) return `${(n / 1000000).toFixed(1).replace(/\.0$/, "")}M`;
    if (n >= 1000) return `${(n / 1000).toFixed(1).replace(/\.0$/, "")}k`;
    return String(n);
  }

  function formatAge(days) {
    if (days === null || days === undefined) return "";
    if (days === 0) return "hoje";
    if (days < 30) return `${days}d`;
    if (days < 365) return `${Math.floor(days / 30)}m`;
    return `${(days / 365).toFixed(1).replace(/\.0$/, "")}a`;
  }

  function renderIconHtml(svc) {
    const color = CATEGORY_COLORS[svc.category] || "#6366f1";
    const text = escapeHtml(initials(svc.name));
    if (!svc.icon_url) {
      return `<span class="icon-fallback" style="color:${color};background:${color}18">${text}</span>`;
    }
    return `<img src="${escapeHtml(svc.icon_url)}" alt="" loading="lazy" onerror="this.style.display='none';this.nextElementSibling.style.display='grid'"><span class="icon-fallback" style="display:none;color:${color};background:${color}18">${text}</span>`;
  }

  const ICONS = {
    globe: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>`,
    git: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M13 6h3a2 2 0 0 1 2 2v7"/><line x1="6" y1="9" x2="6" y2="21"/></svg>`,
    demo: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>`,
    info: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`,
    star: `<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`,
  };

  function renderLinksHtml(svc) {
    const parts = [];
    if (svc.official_url) {
      parts.push(`<a class="link-pill official" href="${escapeHtml(svc.official_url)}" target="_blank" rel="noopener noreferrer">${ICONS.globe}<span>Site Oficial</span></a>`);
    }
    if (svc.git_url) {
      parts.push(`<a class="link-pill" href="${escapeHtml(svc.git_url)}" target="_blank" rel="noopener noreferrer">${ICONS.git}<span>Git</span></a>`);
    }
    if (svc.demo_url) {
      parts.push(`<a class="link-pill demo" href="${escapeHtml(svc.demo_url)}" target="_blank" rel="noopener noreferrer">${ICONS.demo}<span>Demo</span></a>`);
    }
    return parts.join("");
  }

  function renderMetricsRowHtml(svc) {
    const age = formatAge(svc.days_since_commit);
    const starsHtml = svc.stars !== null && svc.stars !== undefined
      ? `<span class="metric-tag" title="${svc.stars.toLocaleString("pt-BR")} estrelas no repositório">${ICONS.star} ${formatCompact(svc.stars)}</span>`
      : "";
    const actText = age ? `${svc.activity_label} · ${age}` : svc.activity_label;
    return `
      <div class="card-metrics-row">
        <span class="score-pill ${escapeHtml(svc.recommendation)}" title="${escapeHtml(svc.score_summary)}">
          <span>${svc.score}/100</span>
          <span>·</span>
          <span>${escapeHtml(svc.recommendation_label)}</span>
        </span>
        ${starsHtml}
        <span class="activity-pill" title="${svc.last_commit ? "Último commit: " + svc.last_commit : svc.activity_label}">
          <span class="activity-dot ${escapeHtml(svc.activity_status)}"></span>
          <span>${escapeHtml(actText)}</span>
        </span>
      </div>
    `;
  }

  function renderCardHtml(svc) {
    const starHtml = svc.popular
      ? `<span class="popular-dot" title="Serviço em destaque">${ICONS.star}</span>`
      : "";
    return `
      <article class="service-card" data-id="${escapeHtml(svc.id)}">
        <div class="card-top">
          <div class="card-identity">
            <div class="card-icon-wrap">${renderIconHtml(svc)}</div>
            <div class="card-title-wrap">
              <div class="card-title-row">
                <h3 class="card-title" title="${escapeHtml(svc.name)}">${escapeHtml(svc.name)}</h3>
                ${starHtml}
              </div>
              <button class="badge" type="button" data-cat-jump="${escapeHtml(svc.category)}">${escapeHtml(svc.category_label)}</button>
            </div>
          </div>
          <button class="details-btn" type="button" data-open-modal="${escapeHtml(svc.id)}" aria-label="Detalhes de ${escapeHtml(svc.name)}" title="Ver Raio-X e detalhes">${ICONS.info}</button>
        </div>
        ${renderMetricsRowHtml(svc)}
        <p class="card-desc">${escapeHtml(svc.description)}</p>
        <div class="card-links">${renderLinksHtml(svc)}</div>
      </article>
    `;
  }

  function renderSidebar() {
    el.headerCountBadge.textContent = `${data.stats.total_services.toLocaleString("pt-BR")} serviços`;
    el.statLeader.textContent = data.stats.leader_count ?? 0;
    el.statRecommended.textContent = data.stats.recommended_count ?? 0;
    el.statNiche.textContent = data.stats.niche_count ?? 0;
    el.statCaution.textContent = data.stats.caution_count ?? 0;
    el.statActive.textContent = data.stats.active_count ?? 0;
    el.statStars10k.textContent = data.stats.stars_10k_count ?? 0;
    el.statPopular.textContent = data.stats.popular_count;
    el.statGit.textContent = data.stats.with_git_url;
    el.statDemo.textContent = data.stats.with_demo_url;
    el.statTotal.textContent = data.stats.total_services;
    el.statCats.textContent = data.stats.total_categories;
    el.statOfficial.textContent = data.stats.with_official_url;
    el.footerStats.textContent = `${data.stats.total_services} serviços · ${data.stats.leader_count} líderes · ${data.stats.active_count} ativos · ${data.stats.caution_count} obsoletos`;

    const buttons = [
      `<button class="cat-btn ${state.category === "all" ? "active" : ""}" data-cat="all" type="button">
        <span class="cat-btn-left"><span class="cat-dot" style="background:var(--accent)"></span><span class="cat-name">Todas as categorias</span></span>
        <span class="cat-count">${data.stats.total_services}</span>
      </button>`,
    ];

    for (const cat of data.categories) {
      const color = CATEGORY_COLORS[cat.id] || "#6366f1";
      buttons.push(`
        <button class="cat-btn ${state.category === cat.id ? "active" : ""}" data-cat="${escapeHtml(cat.id)}" type="button">
          <span class="cat-btn-left"><span class="cat-dot" style="background:${color}"></span><span class="cat-name">${escapeHtml(cat.label)}</span></span>
          <span class="cat-count">${cat.count}</span>
        </button>
      `);
    }

    el.categoryNav.innerHTML = buttons.join("");
  }

  function sortServices(list) {
    const arr = [...list];
    if (state.sort === "score-desc") {
      arr.sort((a, b) => (b.score - a.score) || ((b.stars ?? -1) - (a.stars ?? -1)) || a.name.localeCompare(b.name));
    } else if (state.sort === "score-asc") {
      arr.sort((a, b) => (a.score - b.score) || ((a.stars ?? 0) - (b.stars ?? 0)) || a.name.localeCompare(b.name));
    } else if (state.sort === "stars-desc") {
      arr.sort((a, b) => ((b.stars ?? -1) - (a.stars ?? -1)) || (b.score - a.score));
    } else if (state.sort === "recent") {
      arr.sort((a, b) => {
        const da = a.days_since_commit ?? 999999;
        const db = b.days_since_commit ?? 999999;
        return (da - db) || (b.score - a.score);
      });
    } else {
      arr.sort((a, b) => a.name.localeCompare(b.name));
    }
    return arr;
  }

  function getFilteredServices() {
    const q = state.query.trim().toLowerCase();
    const filtered = allServices.filter((s) => {
      if (state.category !== "all" && s.category !== state.category) return false;
      if (state.rec !== "all" && s.recommendation !== state.rec) return false;
      if (state.filters.popular && !s.popular) return false;
      if (state.filters.git && !s.git_url) return false;
      if (state.filters.demo && !s.demo_url) return false;
      if (state.filters.stars10k && (s.stars ?? 0) < 10000) return false;
      if (state.filters.activeOnly && s.activity_status !== "active") return false;
      if (q) {
        const hay = `${s.name} ${s.description} ${s.category_label} ${s.recommendation_label} ${s.activity_label}`.toLowerCase();
        if (!hay.includes(q)) return false;
      }
      return true;
    });
    return sortServices(filtered);
  }

  function updateHeaderState(filteredCount) {
    const activeCatObj = data.categories.find((c) => c.id === state.category);
    el.activeHeading.textContent = activeCatObj
      ? activeCatObj.label
      : "Todos os Serviços Open-Source & Self-Hosted";

    const hasFilters =
      state.category !== "all" ||
      state.rec !== "all" ||
      state.query.trim() !== "" ||
      Object.values(state.filters).some(Boolean);

    el.resetFiltersBtn.classList.toggle("hidden", !hasFilters);
    el.clearSearchBtn.classList.toggle("hidden", state.query.trim() === "");
    el.resultsCounter.textContent =
      filteredCount === 1 ? "1 serviço" : `${filteredCount.toLocaleString("pt-BR")} serviços`;
  }

  function renderCatalog() {
    const filtered = getFilteredServices();
    updateHeaderState(filtered.length);

    if (filtered.length === 0) {
      el.catalogContainer.innerHTML = "";
      el.emptyState.classList.remove("hidden");
      return;
    }

    el.emptyState.classList.add("hidden");

    if (state.view === "table") {
      const rows = filtered
        .map((s) => {
          const age = formatAge(s.days_since_commit);
          return `
          <tr>
            <td>
              <div class="table-name-cell">
                <span>${escapeHtml(s.name)}</span>
                ${s.popular ? `<span class="popular-dot" title="Destaque">${ICONS.star}</span>` : ""}
              </div>
              <button class="badge" type="button" data-cat-jump="${escapeHtml(s.category)}">${escapeHtml(s.category_label)}</button>
            </td>
            <td>
              <span class="score-pill ${escapeHtml(s.recommendation)}">${s.score}/100 · ${escapeHtml(s.recommendation_label)}</span>
              <div style="margin-top:4px;display:flex;gap:5px;flex-wrap:wrap;">
                ${s.stars !== null ? `<span class="metric-tag">${ICONS.star} ${formatCompact(s.stars)}</span>` : ""}
                <span class="activity-pill"><span class="activity-dot ${escapeHtml(s.activity_status)}"></span>${escapeHtml(age ? `${s.activity_label} · ${age}` : s.activity_label)}</span>
              </div>
            </td>
            <td>${escapeHtml(s.description)}</td>
            <td><div class="table-links-cell">${renderLinksHtml(s)}</div></td>
          </tr>`;
        })
        .join("");

      el.catalogContainer.innerHTML = `
        <div class="table-wrap">
          <table class="catalog-table">
            <thead>
              <tr>
                <th>Serviço</th>
                <th>Score &amp; Saúde</th>
                <th>Descrição</th>
                <th>Links</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      `;
      return;
    }

    if (state.view === "grid") {
      el.catalogContainer.innerHTML = `<div class="cards-grid">${filtered.map(renderCardHtml).join("")}</div>`;
      return;
    }

    // Grouped by category
    const byCat = new Map();
    for (const s of filtered) {
      if (!byCat.has(s.category)) byCat.set(s.category, []);
      byCat.get(s.category).push(s);
    }

    const sections = [];
    for (const cat of data.categories) {
      const list = byCat.get(cat.id);
      if (!list || list.length === 0) continue;
      const color = CATEGORY_COLORS[cat.id] || "#6366f1";
      sections.push(`
        <section class="category-section" id="cat-${escapeHtml(cat.id)}">
          <div class="category-header">
            <h2 class="category-title">
              <span class="cat-dot" style="background:${color};width:9px;height:9px"></span>
              <span>${escapeHtml(cat.label)}</span>
              <span class="category-pill">${list.length}</span>
            </h2>
          </div>
          <div class="cards-grid">${list.map(renderCardHtml).join("")}</div>
        </section>
      `);
    }
    el.catalogContainer.innerHTML = sections.join("");
  }

  function setCategory(catId) {
    state.category = catId;
    document.querySelectorAll(".cat-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.cat === catId);
    });
    renderCatalog();
    window.scrollTo({ top: 0, behavior: "smooth" });
    closeMobileSidebar();
  }

  function resetAllFilters() {
    state.query = "";
    state.category = "all";
    state.rec = "all";
    state.filters = { popular: false, git: false, demo: false, stars10k: false, activeOnly: false };
    el.searchInput.value = "";
    el.filterChips.forEach((c) => c.classList.remove("active"));
    el.recChips.forEach((c) => c.classList.remove("active"));
    document.querySelectorAll(".cat-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.cat === "all");
    });
    renderCatalog();
  }

  function openServiceModal(id) {
    const svc = serviceById.get(id);
    if (!svc) return;
    el.modalIconWrap.innerHTML = renderIconHtml(svc);
    el.modalCategory.textContent = svc.category_label;
    el.modalTitle.textContent = svc.name;
    el.modalDesc.textContent = svc.description;

    const bd = svc.score_breakdown || {};
    const pillars = [
      { label: "Aceitação (Estrelas)", val: bd.popularity ?? 0, max: 40 },
      { label: "Atividade (Commits/PRs)", val: bd.activity ?? 0, max: 35 },
      { label: "Comunidade (Forks/Trend)", val: bd.community ?? 0, max: 15 },
      { label: "Ecossistema (Site/Demo)", val: bd.ecosystem ?? 0, max: 10 },
    ];

    const starsStr = svc.stars !== null ? `${svc.stars.toLocaleString("pt-BR")} ★` : "N/D";
    const forksStr = svc.forks !== null ? `${svc.forks.toLocaleString("pt-BR")} forks` : "N/D";
    const commitStr = svc.last_commit ? `${svc.last_commit} (${formatAge(svc.days_since_commit)})` : svc.activity_label;

    el.modalScoreCard.innerHTML = `
      <div class="modal-score-top">
        <div class="modal-score-main">
          <span class="modal-score-num">${svc.score}/100</span>
          <span class="score-pill ${escapeHtml(svc.recommendation)}">${svc.rating} ★ · ${escapeHtml(svc.recommendation_label)}</span>
        </div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          <span class="metric-tag">${starsStr}</span>
          <span class="metric-tag">${forksStr}</span>
          <span class="activity-pill"><span class="activity-dot ${escapeHtml(svc.activity_status)}"></span>${escapeHtml(commitStr)}</span>
        </div>
      </div>
      <p class="modal-score-summary">${escapeHtml(svc.score_summary)}${bd.penalty ? ` (Penalidade por obsolescência: -${bd.penalty} pts)` : ""}</p>
      <div class="pillars-grid">
        ${pillars
          .map(
            (p) => `
          <div class="pillar-item">
            <div class="pillar-label"><span>${p.label}</span><span>${p.val}/${p.max}</span></div>
            <div class="pillar-track"><div class="pillar-fill" style="width:${Math.round((p.val / p.max) * 100)}%"></div></div>
          </div>`
          )
          .join("")}
      </div>
    `;

    if (svc.features && svc.features.length > 0) {
      el.modalFeaturesList.innerHTML = svc.features.map((f) => `<li>${escapeHtml(f)}</li>`).join("");
      el.modalFeaturesWrap.classList.remove("hidden");
    } else {
      el.modalFeaturesWrap.classList.add("hidden");
    }

    el.modalLinks.innerHTML = renderLinksHtml(svc);
    el.modal.showModal();
  }

  function closeMobileSidebar() {
    el.sidebar.classList.remove("open");
    el.sidebarBackdrop.classList.add("hidden");
    el.mobileMenuBtn.setAttribute("aria-expanded", "false");
  }

  function downloadFile(filename, content, mime) {
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  function handleExport(format) {
    const list = getFilteredServices();
    if (format === "json") {
      downloadFile("servicos-filtrados.json", JSON.stringify(list, null, 2), "application/json;charset=utf-8");
    } else if (format === "csv") {
      const header = ["Nome", "Categoria", "Score", "Nota", "Recomendação", "Estrelas", "Forks", "Último Commit", "Atividade", "Descrição", "Site Oficial", "Repositório Git", "Demo"];
      const esc = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
      const rows = [
        header.map(esc).join(","),
        ...list.map((s) =>
          [
            s.name,
            s.category_label,
            s.score,
            s.rating,
            s.recommendation_label,
            s.stars ?? "",
            s.forks ?? "",
            s.last_commit ?? "",
            s.activity_label,
            s.description,
            s.official_url,
            s.git_url || "",
            s.demo_url || "",
          ]
            .map(esc)
            .join(",")
        ),
      ];
      downloadFile("servicos-filtrados.csv", "\uFEFF" + rows.join("\n"), "text/csv;charset=utf-8");
    } else if (format === "md") {
      const lines = ["# Catálogo de Serviços Filtrados", ""];
      for (const s of list) {
        const links = [
          s.official_url ? `[Site Oficial](${s.official_url})` : null,
          s.git_url ? `[Git](${s.git_url})` : null,
          s.demo_url ? `[Demo](${s.demo_url})` : null,
        ].filter(Boolean).join(" · ");
        const starsTxt = s.stars !== null ? `★ ${s.stars.toLocaleString("pt-BR")}` : "—";
        lines.push(`- **${s.name}** (*${s.category_label}* · Score **${s.score}/100** · ${s.recommendation_label} · ${starsTxt} · ${s.activity_label}): ${s.description} — ${links}`);
      }
      downloadFile("servicos-filtrados.md", lines.join("\n"), "text/markdown;charset=utf-8");
    }
    el.exportMenu.classList.add("hidden");
    el.exportToggleBtn.setAttribute("aria-expanded", "false");
  }

  function initTheme() {
    const saved = localStorage.getItem("catalog-theme");
    const theme = saved || (window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark");
    el.html.setAttribute("data-theme", theme);
  }

  function bindEvents() {
    let searchTimer = null;
    el.searchInput.addEventListener("input", (e) => {
      clearTimeout(searchTimer);
      searchTimer = setTimeout(() => {
        state.query = e.target.value;
        renderCatalog();
      }, 90);
    });

    el.clearSearchBtn.addEventListener("click", () => {
      el.searchInput.value = "";
      state.query = "";
      renderCatalog();
      el.searchInput.focus();
    });

    el.sortSelect.addEventListener("change", (e) => {
      state.sort = e.target.value;
      renderCatalog();
    });

    el.categoryNav.addEventListener("click", (e) => {
      const btn = e.target.closest(".cat-btn");
      if (btn) setCategory(btn.dataset.cat);
    });

    el.catalogContainer.addEventListener("click", (e) => {
      const jump = e.target.closest("[data-cat-jump]");
      if (jump) {
        setCategory(jump.dataset.catJump);
        return;
      }
      const modalTrigger = e.target.closest("[data-open-modal]");
      if (modalTrigger) {
        openServiceModal(modalTrigger.dataset.openModal);
      }
    });

    el.recChips.forEach((chip) => {
      chip.addEventListener("click", () => {
        const rec = chip.dataset.rec;
        state.rec = state.rec === rec ? "all" : rec;
        el.recChips.forEach((c) => c.classList.toggle("active", c.dataset.rec === state.rec));
        renderCatalog();
        closeMobileSidebar();
      });
    });

    el.filterChips.forEach((chip) => {
      chip.addEventListener("click", () => {
        const key = chip.dataset.filter;
        state.filters[key] = !state.filters[key];
        chip.classList.toggle("active", state.filters[key]);
        renderCatalog();
      });
    });

    el.viewButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        state.view = btn.dataset.view;
        el.viewButtons.forEach((b) => b.classList.toggle("active", b === btn));
        renderCatalog();
      });
    });

    el.resetFiltersBtn.addEventListener("click", resetAllFilters);
    el.emptyResetBtn.addEventListener("click", resetAllFilters);

    el.themeToggleBtn.addEventListener("click", () => {
      const next = el.html.getAttribute("data-theme") === "dark" ? "light" : "dark";
      el.html.setAttribute("data-theme", next);
      localStorage.setItem("catalog-theme", next);
    });

    el.mobileMenuBtn.addEventListener("click", () => {
      const opening = !el.sidebar.classList.contains("open");
      el.sidebar.classList.toggle("open", opening);
      el.sidebarBackdrop.classList.toggle("hidden", !opening);
      el.mobileMenuBtn.setAttribute("aria-expanded", String(opening));
    });

    el.sidebarBackdrop.addEventListener("click", closeMobileSidebar);

    el.exportToggleBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const opening = el.exportMenu.classList.contains("hidden");
      el.exportMenu.classList.toggle("hidden", !opening);
      el.exportToggleBtn.setAttribute("aria-expanded", String(opening));
    });

    el.exportMenu.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-export]");
      if (btn) handleExport(btn.dataset.export);
    });

    document.addEventListener("click", (e) => {
      if (!e.target.closest(".export-dropdown")) {
        el.exportMenu.classList.add("hidden");
        el.exportToggleBtn.setAttribute("aria-expanded", "false");
      }
    });

    el.modalCloseBtn.addEventListener("click", () => el.modal.close());
    el.modal.addEventListener("click", (e) => {
      if (e.target === el.modal) el.modal.close();
    });

    window.addEventListener("scroll", () => {
      el.backToTopBtn.classList.toggle("hidden", window.scrollY < 450);
    }, { passive: true });

    el.backToTopBtn.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });

    document.addEventListener("keydown", (e) => {
      if ((e.key === "/" || ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k")) &&
          document.activeElement !== el.searchInput) {
        e.preventDefault();
        el.searchInput.focus();
        el.searchInput.select();
      } else if (e.key === "Escape" && document.activeElement === el.searchInput && el.searchInput.value) {
        el.searchInput.value = "";
        state.query = "";
        renderCatalog();
      }
    });
  }

  initTheme();
  renderSidebar();
  bindEvents();
  renderCatalog();
})();
