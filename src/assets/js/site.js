// Tutor Lawrence — small behaviours only. The site works without this file.
(function () {
  document.documentElement.classList.add("js");

  // Mobile menu
  var button = document.querySelector(".menu-button");
  var nav = document.getElementById("site-nav");
  if (button && nav) {
    button.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      button.setAttribute("aria-expanded", open ? "true" : "false");
      button.textContent = open ? "Close" : "Menu";
    });
  }

  // Marked page: tabs switch the example; corrections are written in once.
  document.querySelectorAll("[data-marked]").forEach(function (block) {
    var tabs = block.querySelectorAll('[role="tab"]');
    var panels = block.querySelectorAll('[role="tabpanel"]');
    function show(tab) {
      tabs.forEach(function (t) {
        var on = t === tab;
        t.setAttribute("aria-selected", on ? "true" : "false");
        t.tabIndex = on ? 0 : -1;
      });
      panels.forEach(function (p) {
        var on = p.id === tab.getAttribute("aria-controls");
        p.hidden = !on;
        p.classList.remove("play");
        if (on) { void p.offsetWidth; p.classList.add("play"); }
      });
    }
    tabs.forEach(function (tab, i) {
      tab.addEventListener("click", function () { show(tab); });
      tab.addEventListener("keydown", function (e) {
        if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
        var next = tabs[(i + (e.key === "ArrowRight" ? 1 : tabs.length - 1)) % tabs.length];
        next.focus();
        show(next);
      });
    });
    var first = block.querySelector('[role="tabpanel"]:not([hidden])');
    if (first) first.classList.add("play");
  });
})();
