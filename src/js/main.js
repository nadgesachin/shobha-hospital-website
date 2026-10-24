/* Suvacha Healthcare — site behaviour. No dependencies. */
(function () {
  "use strict";
  document.documentElement.classList.remove("no-js");
  var CFG = window.SUVACHA || {};
  var LOCALE = CFG.lang || "en-IN";
  var BASE = CFG.base || "";
  // UI text: English is the key; Hindi/Marathi pages pass a table in CFG.t. {x} placeholders get vars.
  function T(key, vars) {
    var out = (CFG.t && CFG.t[key]) || key;
    for (var k in vars || {}) out = out.split("{" + k + "}").join(vars[k]);
    return out;
  }
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ---------- Hosting badge (Netlify free tier injects one at bottom-right) ---------- */
  function checkBadge() {
    if (document.getElementById("nl-badge-frame")) {
      document.documentElement.classList.add("has-host-badge");
      return true;
    }
  }
  if (!checkBadge() && "MutationObserver" in window) {
    var mo = new MutationObserver(function () { if (checkBadge()) mo.disconnect(); });
    mo.observe(document.body, { childList: true });
    setTimeout(function () { mo.disconnect(); }, 15000);
  }

  /* ---------- Sticky header shadow + back-to-top ---------- */
  var header = $(".header");
  var toTop = $(".to-top");
  function onScroll() {
    var y = window.scrollY;
    if (header) header.classList.toggle("is-scrolled", y > 8);
    if (toTop) toTop.classList.toggle("is-visible", y > 700);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  // first measurement after load, so it never forces a layout during the initial render
  window.addEventListener("load", onScroll);
  if (toTop) toTop.addEventListener("click", function () { window.scrollTo({ top: 0 }); });

  /* ---------- Mobile drawer ---------- */
  var drawer = $(".drawer");
  var toggle = $(".menu-toggle");
  function setDrawer(open) {
    if (!drawer) return;
    drawer.classList.toggle("is-open", open);
    drawer.setAttribute("aria-hidden", String(!open));
    toggle.setAttribute("aria-expanded", String(open));
    document.body.style.overflow = open ? "hidden" : "";
    if (open) $(".drawer__close", drawer).focus(); else toggle.focus();
  }
  if (toggle) toggle.addEventListener("click", function () { setDrawer(true); });
  $$("[data-close-drawer]").forEach(function (el) { el.addEventListener("click", function () { setDrawer(false); }); });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && drawer && drawer.classList.contains("is-open")) setDrawer(false);
  });

  /* ---------- Desktop dropdown (click / keyboard) ---------- */
  $$(".nav__item--has-menu").forEach(function (item) {
    var btn = $(".nav__link", item);
    btn.addEventListener("click", function () {
      var open = !item.classList.contains("is-open");
      item.classList.toggle("is-open", open);
      btn.setAttribute("aria-expanded", String(open));
    });
    item.addEventListener("mouseleave", function () {
      item.classList.remove("is-open");
      btn.setAttribute("aria-expanded", "false");
    });
  });
  document.addEventListener("click", function (e) {
    $$(".nav__item--has-menu.is-open").forEach(function (item) {
      if (!item.contains(e.target)) item.classList.remove("is-open");
    });
  });

  /* ---------- Open now (clinic time is IST, regardless of visitor timezone) ---------- */
  function istNow() {
    var parts = new Intl.DateTimeFormat("en-GB", {
      timeZone: "Asia/Kolkata", weekday: "short", hour: "2-digit", minute: "2-digit", hour12: false
    }).formatToParts(new Date());
    var get = function (t) { return (parts.find(function (p) { return p.type === t; }) || {}).value; };
    var dow = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].indexOf(get("weekday"));
    return { dow: dow, mins: (+get("hour") % 24) * 60 + +get("minute") };
  }
  function toMins(hhmm) { var p = hhmm.split(":"); return +p[0] * 60 + +p[1]; }
  if (CFG.hours) {
    var now = istNow();
    var today = CFG.hours.find(function (h) { return h.dow.indexOf(now.dow) !== -1; });
    var open = today && now.mins >= toMins(today.open) && now.mins < toMins(today.close);
    $$("[data-open-badge]").forEach(function (el) {
      el.classList.toggle("is-open", !!open);
      el.textContent = open ? T("Open now · until {time}", { time: today.label.split("–")[1].trim() }) : T("Closed now");
    });
    $$("[data-hours-row]").forEach(function (row) {
      var days = row.getAttribute("data-hours-row").split(",").map(Number);
      row.classList.toggle("is-today", days.indexOf(now.dow) !== -1);
    });
  }

  var REDUCED = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Stagger: siblings inside a grid reveal one after another ---------- */
  $$(".pillars, .services-grid, .tiles, .doctors-grid, .slider, .why-grid, .why-mini, .journey, .tool-promos, .contact-cards, .mv-grid, .reviews").forEach(function (grid) {
    var i = 0;
    Array.prototype.forEach.call(grid.children, function (el) {
      if (el.classList.contains("reveal")) el.style.setProperty("--i", i++);
    });
  });

  /* ---------- Scroll reveal ---------- */
  var reveals = $$(".reveal, .reveal-line");
  if ("IntersectionObserver" in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add("is-in"); io.unobserve(en.target); }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("is-in"); });
  }

  /* ---------- Count-up numbers (stats band) ---------- */
  var counters = $$("[data-count]");
  if (counters.length && !REDUCED && "IntersectionObserver" in window) {
    counters.forEach(function (el) { el.textContent = "0"; });
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        cio.unobserve(en.target);
        var el = en.target, to = +el.getAttribute("data-count"), t0 = null, dur = 1400;
        (function step(t) {
          if (t0 === null) t0 = t;
          var p = Math.min(1, (t - t0) / dur), eased = 1 - Math.pow(1 - p, 3);
          el.textContent = Math.round(to * eased);
          if (p < 1) requestAnimationFrame(step);
        })(performance.now());
      });
    }, { threshold: 0.6 });
    counters.forEach(function (el) { cio.observe(el); });
  }

  /* ---------- Gentle parallax on the hero picture ---------- */
  var par = $("[data-parallax]");
  if (par && !REDUCED) {
    var ticking = false;
    var update = function () {
      ticking = false;
      var r = par.getBoundingClientRect();
      if (r.bottom < 0 || r.top > innerHeight) return;
      var shift = Math.max(-36, Math.min(36, (r.top + r.height / 2 - innerHeight / 2) * -0.07));
      par.style.transform = "translate3d(0," + shift.toFixed(1) + "px,0)";
    };
    window.addEventListener("scroll", function () {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    window.addEventListener("load", update);
  }

  /* ---------- Swipe hint: on touch screens, nudge the doctor slider once ---------- */
  var touch = window.matchMedia && matchMedia("(hover: none) and (pointer: coarse)").matches;
  if (touch && !REDUCED && "IntersectionObserver" in window) {
    $$(".slider").forEach(function (track) {
      var sio = new IntersectionObserver(function (entries) {
        if (!entries[0].isIntersecting) return;
        sio.disconnect();
        if (track.scrollLeft > 0 || track.scrollWidth <= track.clientWidth) return;
        setTimeout(function () { track.scrollBy({ left: 90, behavior: "smooth" }); }, 700);
        setTimeout(function () { track.scrollBy({ left: -90, behavior: "smooth" }); }, 1500);
      }, { threshold: 0.6 });
      sio.observe(track);
    });
  }

  /* ---------- Doctor filter ---------- */
  var chips = $$("[data-filter]");
  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      var f = chip.getAttribute("data-filter");
      chips.forEach(function (c) { c.setAttribute("aria-pressed", String(c === chip)); });
      $$("[data-tags]").forEach(function (card) {
        card.hidden = f !== "all" && card.getAttribute("data-tags").split("|").indexOf(f) === -1;
      });
    });
  });

  /* ---------- Horizontal slider buttons ---------- */
  $$("[data-slider]").forEach(function (wrap) {
    var track = $(".slider", wrap);
    $$("[data-dir]", wrap).forEach(function (b) {
      b.addEventListener("click", function () {
        var card = track.firstElementChild;
        var step = card ? card.getBoundingClientRect().width + 24 : 300;
        track.scrollBy({ left: step * +b.getAttribute("data-dir"), behavior: "smooth" });
      });
    });
  });

  /* ---------- WhatsApp float hint (once per session) ---------- */
  var wa = $(".wa-float");
  if (wa) {
    try {
      if (!sessionStorage.getItem("wa-hint")) {
        setTimeout(function () { wa.classList.add("is-hinting"); }, 4000);
        setTimeout(function () { wa.classList.remove("is-hinting"); }, 9000);
        sessionStorage.setItem("wa-hint", "1");
      }
    } catch (e) { /* storage blocked: skip the hint */ }
  }

  /* ---------- Booking form -> WhatsApp ---------- */
  $$("form[data-booking]").forEach(function (form) {
    var date = form.querySelector("[name=date]");
    if (date) {
      var d = new Date();
      date.min = new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
    }
    // Pre-select service / doctor from ?service=slug&doctor=slug
    var params = new URLSearchParams(location.search);
    ["service", "doctor"].forEach(function (k) {
      var v = params.get(k), sel = form.querySelector("[name=" + k + "]");
      if (v && sel && sel.querySelector('option[value="' + v + '"]')) sel.value = v;
    });

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!form.reportValidity()) return;
      var fd = new FormData(form);
      var label = function (name) {
        var sel = form.querySelector("[name=" + name + "]");
        return sel && sel.selectedIndex > 0 ? sel.options[sel.selectedIndex].text : "";
      };
      var lines = [
        T("Namaste Suvacha Healthcare 🙏"),
        T("I would like to book an appointment."),
        "",
        "*" + T("Name") + ":* " + fd.get("name"),
        "*" + T("Phone") + ":* " + fd.get("phone")
      ];
      if (label("service")) lines.push("*" + T("Service") + ":* " + label("service"));
      if (label("doctor")) lines.push("*" + T("Preferred doctor") + ":* " + label("doctor"));
      if (fd.get("mode")) lines.push("*" + T("Consultation") + ":* " + T(fd.get("mode")));
      if (fd.get("date")) {
        var pd = new Date(fd.get("date") + "T00:00:00");
        lines.push("*" + T("Preferred date") + ":* " + pd.toLocaleDateString(LOCALE, { weekday: "short", day: "numeric", month: "short", year: "numeric" }));
      }
      if (fd.get("time")) {
        var ts = form.querySelector("[name=time]");
        lines.push("*" + T("Preferred time") + ":* " + ts.options[ts.selectedIndex].text);
      }
      if (fd.get("message")) lines.push("", "*" + T("Concern") + ":* " + fd.get("message"));
      var url = "https://wa.me/" + CFG.whatsapp + "?text=" + encodeURIComponent(lines.join("\n"));
      window.open(url, "_blank", "noopener");
    });
  });

  /* ---------- Pregnancy & fertility calculators ---------- */
  var DAY = 864e5;
  function parseDate(s) { var p = s.split("-"); return new Date(+p[0], +p[1] - 1, +p[2]); }
  function addDays(d, n) { return new Date(d.getFullYear(), d.getMonth(), d.getDate() + n); }
  function daysBetween(a, b) { return Math.round((b - a) / DAY); }
  function fmt(d, noYear) {
    var o = { day: "numeric", month: "short" };
    if (!noYear) o.year = "numeric";
    return d.toLocaleDateString(LOCALE, o);
  }
  function today0() { var t = new Date(); return new Date(t.getFullYear(), t.getMonth(), t.getDate()); }
  function waUrl(text) { return "https://wa.me/" + CFG.whatsapp + "?text=" + encodeURIComponent(text); }
  var ICON_CAL = '<svg class="icon" viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/></svg>';
  var ICON_WA = $(".wa-float__btn svg") ? $(".wa-float__btn svg").outerHTML : "";

  // Antenatal scan & test windows (weeks), as listed on the Pregnancy & Maternal Care page.
  var MILESTONES = [
    { t: T("Early pregnancy scan"), d: T("Confirms the pregnancy, heartbeat and dates"), s: 6, e: 8 },
    { t: T("NT scan"), d: T("Nuchal translucency screening"), s: 11, e: 13 },
    { t: T("Anomaly / Level-2 scan"), d: T("Detailed check of baby’s growth and organs"), s: 18, e: 20 },
    { t: T("Glucose tolerance test (GTT)"), d: T("Screening for gestational diabetes"), s: 24, e: 28 },
    { t: T("Growth scan"), d: T("Baby’s growth and fluid check"), s: 28, e: 28 },
    { t: T("Growth scan"), d: T("Baby’s growth and position"), s: 32, e: 32 },
    { t: T("Growth scan"), d: T("Final growth and position check"), s: 36, e: 36 },
    { t: T("Full term"), d: T("Baby can arrive any time — keep your hospital bag ready"), s: 37, e: 40 }
  ];

  function readTool(form) {
    var lmpVal = form.lmp.value;
    var cycle = parseInt(form.cycle.value || "28", 10);
    if (!lmpVal) return { error: T("Please enter the first day of your last period.") };
    if (isNaN(cycle) || cycle < 21 || cycle > 45) return { error: T("Cycle length should be between 21 and 45 days.") };
    var lmp = parseDate(lmpVal);
    if (lmp > today0()) return { error: T("That date is in the future — please check it.") };
    return { lmp: lmp, cycle: cycle };
  }
  function showResult(form, html) {
    var box = $('[data-result="' + form.getAttribute("data-tool") + '"]');
    box.innerHTML = html;
    box.hidden = false;
    box.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function calcEdd(form) {
    var v = readTool(form);
    if (v.error) return showResult(form, '<p class="tool-error">' + v.error + "</p>");
    var start = addDays(v.lmp, v.cycle - 28); // cycle-adjusted dating
    var edd = addDays(start, 280);
    var ga = daysBetween(start, today0());
    if (ga > 42 * 7) return showResult(form, '<p class="tool-error">' + T("That date is more than 42 weeks ago — please check it.") + "</p>");
    ga = Math.max(ga, 0);
    var wk = Math.floor(ga / 7), dy = ga % 7;
    var tri = T(wk < 14 ? "1st trimester" : wk < 28 ? "2nd trimester" : "3rd trimester");
    var left = daysBetween(today0(), edd);
    var pct = Math.min(100, Math.round(ga / 280 * 100));
    var rows = MILESTONES.map(function (m) {
      var s = m.s * 7, e = m.e * 7 + 6;
      var cls = ga > e ? "is-done" : ga >= s ? "is-now" : "";
      var when = m.s === m.e ? T("Week {n}", { n: m.s }) : T("Weeks {a}–{b}", { a: m.s, b: m.e });
      var range = fmt(addDays(start, s), true) + (m.s === m.e ? "" : " – " + fmt(addDays(start, e), true));
      var tag = cls === "is-done" ? T("Done ✓") : cls === "is-now" ? T("Due now · {range}", { range: range }) : range;
      return '<li class="' + cls + '"><div><strong>' + m.t + "</strong><small>" + when + " · " + m.d +
        '</small></div><span class="when">' + tag + "</span></li>";
    }).join("");
    var status = left >= 0 ? T("{n} days to go", { n: left }) : T("Past your due date by {n} days — please consult your doctor", { n: -left });
    var preg = T("{w} weeks {d} days pregnant", { w: wk, d: dy });
    var msg = T("Namaste Suvacha Healthcare 🙏") + "\n" +
      T("My estimated due date is {date} ({preg}). I would like to book an antenatal consultation.", { date: fmt(edd), preg: preg });
    showResult(form,
      '<div class="edd-hero"><small>' + T("Estimated due date") + "</small><strong>" + fmt(edd) + "</strong>" +
      "<span>" + preg + " · " + tri + " · " + status + "</span>" +
      '<div class="progress" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="' + pct + '" aria-label="' + T("Pregnancy progress") + '"><i style="width:' + pct + '%"></i></div>' +
      '<div class="progress-labels"><span>' + T("Week {n}", { n: 0 }) + "</span><span>" + T("Week {n}", { n: 20 }) + "</span><span>" + T("Week {n}", { n: 40 }) + "</span></div></div>" +
      '<h3 style="font-size:1.3rem;margin:0">' + T("Your scan & test timeline") + '</h3><ul class="timeline">' + rows + "</ul>" +
      '<div class="tool-actions"><a class="btn btn--coral btn--sm" href="' + BASE + '/appointment/?service=pregnancy-maternal-care">' + ICON_CAL +
      " " + T("Book antenatal visit") + '</a><a class="btn btn--wa btn--sm" target="_blank" rel="noopener" href="' + waUrl(msg) + '">' + ICON_WA + " " + T("Share on WhatsApp") + "</a></div>");
  }

  function calcOvulation(form) {
    var v = readTool(form);
    if (v.error) return showResult(form, '<p class="tool-error">' + v.error + "</p>");
    var t = today0();
    var k = Math.max(0, Math.floor(daysBetween(v.lmp, t) / v.cycle));
    var inWindow = null;
    var items = [0, 1, 2].map(function (i) {
      var period = addDays(v.lmp, (k + i) * v.cycle);
      var next = addDays(period, v.cycle);
      var ov = addDays(next, -14);
      var fs = addDays(ov, -5), fe = addDays(ov, 1);
      if (!inWindow && t >= fs && t <= fe) inWindow = fe;
      return "<li><h4>" + T("Cycle starting {date}", { date: fmt(period, true) }) + "</h4>" +
        '<div class="cycle-row is-key"><span>' + T("Fertile window") + "</span><b>" + fmt(fs, true) + " – " + fmt(fe, true) + "</b></div>" +
        '<div class="cycle-row is-key"><span>' + T("Likely ovulation") + "</span><b>" + fmt(ov) + "</b></div>" +
        '<div class="cycle-row"><span>' + T("Next period expected") + "</span><b>" + fmt(next) + "</b></div></li>";
    }).join("");
    var now = inWindow ? '<p class="block__note" style="margin:0 0 16px">🌸 <span>' + T("You are in your fertile window now (until {date}).", { date: fmt(inWindow, true) }) + "</span></p>" : "";
    var msg = T("Namaste Suvacha Healthcare 🙏") + "\n" + T("We are planning a pregnancy and would like to book a fertility consultation.");
    showResult(form, now + '<ul class="cycle-list">' + items + "</ul>" +
      '<p class="form-note">' + T("Trying for 12 months without success (or 6 months if you are over 35)? A fertility evaluation for both partners is recommended.") + "</p>" +
      '<div class="tool-actions"><a class="btn btn--sm" href="' + BASE + '/appointment/?service=infertility-reproductive-health">' + ICON_CAL +
      " " + T("Book fertility consultation") + '</a><a class="btn btn--wa btn--sm" target="_blank" rel="noopener" href="' + waUrl(msg) + '">' + ICON_WA + " " + T("Ask on WhatsApp") + "</a></div>");
  }

  $$("form[data-tool]").forEach(function (form) {
    var max = new Date(today0() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 10);
    form.lmp.max = max;
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      (form.getAttribute("data-tool") === "edd" ? calcEdd : calcOvulation)(form);
    });
  });
})();
