/* Steady — shared front-end behavior
   - Wires every [data-lead-form] to insert into the Supabase steady_leads table
   - Handles the mobile nav toggle
   Depends on: @supabase/supabase-js (CDN) + config.js (SUPABASE_URL, SUPABASE_KEY)
*/
(function () {
  "use strict";

  // --- Supabase client ---------------------------------------------------
  var client = null;
  try {
    if (window.supabase && typeof SUPABASE_URL !== "undefined" && typeof SUPABASE_KEY !== "undefined") {
      client = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
    }
  } catch (e) {
    console.error("Steady: could not init Supabase", e);
  }

  // --- Lead capture forms ------------------------------------------------
  function wireForm(form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();

      var msg = form.querySelector(".form-msg");
      var btn = form.querySelector('button[type="submit"]');
      var data = Object.fromEntries(new FormData(form).entries());
      var setMsg = function (text, kind) {
        if (!msg) return;
        msg.textContent = text;
        msg.className = "form-msg " + (kind || "");
      };

      if (!data.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
        setMsg("Please enter a valid email.", "err");
        return;
      }

      // "source" comes from a select in the form, else the form's data attribute
      var source = data.source || form.getAttribute("data-lead-form") || null;

      var row = {
        name: data.name ? data.name.trim() : null,
        email: data.email.trim(),
        source: source
      };

      var originalLabel = btn ? btn.textContent : "";
      if (btn) { btn.disabled = true; btn.textContent = "Sending…"; }
      setMsg("", "");

      if (!client) {
        // Fail gracefully if the CDN/config didn't load
        setMsg("We couldn't reach the server. Please email hello@steadynutrition.co.", "err");
        if (btn) { btn.disabled = false; btn.textContent = originalLabel; }
        return;
      }

      client.from("steady_leads").insert(row).then(function (res) {
        if (res.error) {
          console.error("Steady: insert failed", res.error);
          setMsg("Something went wrong — please try again in a moment.", "err");
          if (btn) { btn.disabled = false; btn.textContent = originalLabel; }
        } else {
          form.reset();
          setMsg("You're in — check your inbox.", "ok");
          if (btn) { btn.textContent = "Done ✓"; }
        }
      });
    });
  }

  // --- Scroll reveal (progressive enhancement) ---------------------------
  function setupReveal() {
    try {
      var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      if (reduce || !("IntersectionObserver" in window)) return;

      var sel = ".section-head, .cause-card, .card, .program, .step, .tl-item, " +
                ".principle, .feature-card, .quote, .stat, .callout, .form-band, " +
                ".gallery img, .coach-band > div, .story-figure, .quiz-card, .fit-col";
      var nodes = [].slice.call(document.querySelectorAll(sel));
      if (!nodes.length) return;

      var vh = window.innerHeight || document.documentElement.clientHeight;
      var observed = [];
      nodes.forEach(function (el) {
        // Don't hide anything already in view — avoids any flash-of-hidden.
        if (el.getBoundingClientRect().top < vh * 0.92) return;
        el.classList.add("reveal");
        observed.push(el);
      });
      if (!observed.length) return;

      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); }
        });
      }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
      observed.forEach(function (el) { io.observe(el); });

      // Safety net: never leave anything hidden.
      setTimeout(function () { observed.forEach(function (el) { el.classList.add("in"); }); }, 1800);
    } catch (e) { /* content stays visible on any error */ }
  }

  // --- Init --------------------------------------------------------------
  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-lead-form]").forEach(wireForm);
    setupReveal();
  });
})();
