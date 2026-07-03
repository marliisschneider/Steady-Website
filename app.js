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

  // --- Init --------------------------------------------------------------
  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-lead-form]").forEach(wireForm);
  });
})();
