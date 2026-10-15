(function () {
  "use strict";
  var views = Array.prototype.slice.call(document.querySelectorAll("[data-view]"));
  var navLinks = Array.prototype.slice.call(document.querySelectorAll("nav a"));
  var head = document.querySelector(".site-head");
  var pendingQ = null;   /* search to apply when a "papers on ..." link opens Publications */
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[data-q]");
    if (a) pendingQ = a.getAttribute("data-q");
  });
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };

  /* gallery: size each photo by its own aspect ratio so portrait photos are not cropped */
  Array.prototype.forEach.call(document.querySelectorAll(".gallery img"), function (img) {
    function fit() {
      if (!img.naturalWidth) return;
      var r = img.naturalWidth / img.naturalHeight;
      img.parentNode.style.aspectRatio = String(r);
    }
    if (img.complete) fit();
    img.addEventListener("load", fit);
  });

  /* Missing images (e.g. before the first image import) fall back gracefully */
  Array.prototype.forEach.call(document.querySelectorAll("img[data-fallback]"), function (img) {
    function miss() {
      var alt = img.getAttribute("data-alt");     /* e.g. a lab photo not imported yet: use a local photo instead */
      if (alt) { img.removeAttribute("data-alt"); img.src = alt; return; }
      img.classList.add("img-missing");
    }
    if (img.complete && img.naturalWidth === 0) miss();
    img.addEventListener("error", miss);
  });

  function setHeadHeight() {
    var fixedSide = getComputedStyle(head).position === "fixed";   /* sidebar layout */
    document.documentElement.style.setProperty("--head-h", (fixedSide ? 0 : head.offsetHeight) + "px");
  }
  setHeadHeight();
  window.addEventListener("resize", setHeadHeight);

  /* header shrinks once the page is scrolled (themes that style .compact) */
  var compact = false;
  function onScroll() {
    /* hysteresis wider than the header's size change, so shrinking never flips it back */
    var y = window.scrollY;
    var c = compact ? y > 30 : y > 120;
    if (c !== compact) { compact = c; head.classList.toggle("compact", c); setTimeout(setHeadHeight, 220); }
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------- routing: #home, #research, #pub-2019, #research-community, #contact ... ---------- */
  function route() {
    var id = decodeURIComponent(location.hash.slice(1)) || "home";
    var target = document.getElementById(id);
    var view = target && target.closest("[data-view]");
    if (target && !view) {           /* e.g. #contact in the footer: stay on the page, just scroll */
      if (!views.some(function (v) { return v.classList.contains("active"); })) views[0].classList.add("active");
      requestAnimationFrame(function () { target.scrollIntoView({ block: "start" }); });
      return;
    }
    if (!view) { view = views[0]; target = null; }
    views.forEach(function (v) { v.classList.toggle("active", v === view); });
    navLinks.forEach(function (a) {
      if (a.getAttribute("href") === "#" + view.id) a.setAttribute("aria-current", "page");
      else a.removeAttribute("aria-current");
    });
    if (view.id === "publications" && pendingQ !== null) {
      search.value = pendingQ; pendingQ = null;
      type = "all";
      typeBtns.forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.typeBtn === "all")); });
      applyFilter();
    }
    if (target && target !== view) {
      if (view.id === "publications") resetFilters();
      requestAnimationFrame(function () { target.scrollIntoView({ block: "start" }); });
    } else {
      window.scrollTo(0, 0);
      requestAnimationFrame(function () { window.scrollTo(0, 0); });  /* undo the browser's own jump to #id */
    }
  }
  window.addEventListener("hashchange", route);

  /* ---------- research language ---------- */
  var research = document.getElementById("research");
  var langBtns = Array.prototype.slice.call(document.querySelectorAll("[data-lang-btn]"));
  function setLang(lang) {
    research.classList.toggle("lang-en", lang === "en");
    research.classList.toggle("lang-ja", lang === "ja");
    langBtns.forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.langBtn === lang)); });
    store.set("research-lang", lang);
  }
  langBtns.forEach(function (b) { b.addEventListener("click", function () { setLang(b.dataset.langBtn); }); });
  setLang(store.get("research-lang") || ((navigator.language || "").indexOf("ja") === 0 ? "ja" : "en"));

  /* ---------- publications search & filter ---------- */
  var search = document.getElementById("pub-search");
  var typeBtns = Array.prototype.slice.call(document.querySelectorAll("[data-type-btn]"));
  var groups = Array.prototype.slice.call(document.querySelectorAll(".year-group"));
  var items = Array.prototype.slice.call(document.querySelectorAll("#pub-groups .pub"));
  var countEl = document.getElementById("pub-count");
  var emptyEl = document.getElementById("pub-empty");
  var type = "all";
  items.forEach(function (li) { li._text = li.textContent.toLowerCase().replace(/\s+/g, " "); });

  function applyFilter() {
    var terms = search.value.toLowerCase().trim().split(/\s+/).filter(Boolean);
    var shown = 0;
    items.forEach(function (li) {
      var ok = (type === "all" || li.dataset.type === type) &&
        terms.every(function (t) { return li._text.indexOf(t) !== -1; });
      li.hidden = !ok;
      if (ok) shown++;
    });
    groups.forEach(function (g) { g.hidden = !g.querySelector(".pub:not([hidden])"); });
    emptyEl.hidden = shown !== 0;
    countEl.textContent = (terms.length || type !== "all") ? "Showing " + shown + " of " + items.length : "";
  }
  function resetFilters() {
    if (!search.value && type === "all") return;
    search.value = ""; type = "all";
    typeBtns.forEach(function (b) { b.setAttribute("aria-pressed", String(b.dataset.typeBtn === "all")); });
    applyFilter();
  }
  search.addEventListener("input", applyFilter);
  typeBtns.forEach(function (b) {
    b.addEventListener("click", function () {
      type = b.dataset.typeBtn;
      typeBtns.forEach(function (x) { x.setAttribute("aria-pressed", String(x === b)); });
      applyFilter();
    });
  });
  document.getElementById("year-jump").addEventListener("change", function () {
    if (this.value) { location.hash = this.value; this.value = ""; }
  });

  route();
})();
