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
        source: source,
        message: data.message ? data.message.trim() : null
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
                ".gallery img, .coach-band > div, .story-figure, .quiz-card, .fit-col, " +
                ".viz-card, .figure";
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

/* --- Ask Steady: floating chat widget grounded in the Learn library ------
   Talks to the /ask endpoint on the SteadyLeadResearcher service (main.py).
   Reads window.STEADY_ASK_API if set, else localhost in dev / Render live. */
(function () {
  "use strict";

  var API = window.STEADY_ASK_API ||
    ((location.hostname === "localhost" || location.hostname === "127.0.0.1")
      ? "http://localhost:8000"
      : "https://steady-lead-researcher.onrender.com");

  var css =
    ".ask-fab{position:fixed;right:20px;bottom:20px;z-index:9000;display:inline-flex;align-items:center;gap:8px;" +
    "background:#14352a;color:#f7f4ec;border:none;border-radius:100px;padding:13px 20px;font-family:Inter,sans-serif;" +
    "font-weight:650;font-size:0.95rem;cursor:pointer;box-shadow:0 8px 24px rgba(20,53,42,0.28);transition:transform .15s ease}" +
    ".ask-fab:hover{transform:translateY(-2px)}" +
    ".ask-panel{position:fixed;right:20px;bottom:20px;z-index:9001;width:370px;max-width:calc(100vw - 32px);height:540px;" +
    "max-height:calc(100vh - 40px);background:#f7f4ec;border-radius:18px;box-shadow:0 24px 60px rgba(20,53,42,0.34);" +
    "display:none;flex-direction:column;overflow:hidden;font-family:Inter,sans-serif}" +
    ".ask-panel.open{display:flex}" +
    ".ask-head{background:#14352a;color:#f7f4ec;padding:15px 18px;display:flex;justify-content:space-between;align-items:center}" +
    ".ask-head h4{margin:0;font-family:Fraunces,serif;font-size:1.15rem}" +
    ".ask-head .sub{font-size:0.72rem;opacity:0.75;display:block;margin-top:2px}" +
    ".ask-close{background:none;border:none;color:#f7f4ec;font-size:1.5rem;line-height:1;cursor:pointer;opacity:0.85}" +
    ".ask-body{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:12px}" +
    ".ask-msg{max-width:85%;padding:11px 14px;border-radius:14px;font-size:0.92rem;line-height:1.5;white-space:pre-wrap}" +
    ".ask-msg.steady{background:#fff;color:#1f2a1e;align-self:flex-start;border:1px solid rgba(20,53,42,0.08)}" +
    ".ask-msg.user{background:#14352a;color:#f7f4ec;align-self:flex-end}" +
    ".ask-msg.err{background:#f6e0d6;color:#8a3324;align-self:flex-start}" +
    ".ask-typing{align-self:flex-start;color:#6b7d6a;font-size:0.88rem;font-style:italic}" +
    ".ask-foot{padding:12px;border-top:1px solid rgba(20,53,42,0.1);display:flex;gap:8px}" +
    ".ask-foot input{flex:1;border:1px solid rgba(20,53,42,0.18);border-radius:10px;padding:10px 12px;" +
    "font-family:Inter,sans-serif;font-size:0.92rem;background:#fff}" +
    ".ask-foot button{background:#2d6a4f;color:#fff;border:none;border-radius:10px;padding:0 16px;font-weight:650;cursor:pointer}" +
    ".ask-foot button:disabled{opacity:0.5;cursor:default}" +
    ".ask-disc{font-size:0.68rem;color:#8a978a;text-align:center;padding:0 12px 10px}";

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text !== undefined) e.textContent = text;
    return e;
  }

  function init() {
    var style = document.createElement("style");
    style.textContent = css;
    document.head.appendChild(style);

    var fab = el("button", "ask-fab");
    fab.innerHTML = "💬 Ask Steady";
    fab.setAttribute("aria-label", "Ask Steady a nutrition question");

    var panel = el("div", "ask-panel");
    panel.innerHTML =
      '<div class="ask-head"><div><h4>Ask Steady</h4>' +
      '<span class="sub">Answers from the Steady library</span></div>' +
      '<button class="ask-close" aria-label="Close">×</button></div>' +
      '<div class="ask-body"></div>' +
      '<div class="ask-foot"><input type="text" placeholder="Ask about energy, gut, blood sugar…" ' +
      'aria-label="Your question"><button type="button">Send</button></div>' +
      '<p class="ask-disc">Nutrition education, not medical advice. For symptoms, see a doctor.</p>';

    document.body.appendChild(fab);
    document.body.appendChild(panel);

    var body = panel.querySelector(".ask-body");
    var input = panel.querySelector(".ask-foot input");
    var sendBtn = panel.querySelector(".ask-foot button");
    var greeted = false;

    function scrollDown() { body.scrollTop = body.scrollHeight; }
    function addMsg(cls, text) { var m = el("div", "ask-msg " + cls, text); body.appendChild(m); scrollDown(); return m; }

    function open() {
      panel.classList.add("open");
      fab.style.display = "none";
      if (!greeted) {
        addMsg("steady", "Hi — I'm Steady. Ask me anything about energy, blood sugar, gut, inflammation, sleep, or how to eat better. I answer from the Steady library.");
        greeted = true;
      }
      input.focus();
    }
    function close() { panel.classList.remove("open"); fab.style.display = "inline-flex"; }

    function send() {
      var q = input.value.trim();
      if (!q) return;
      addMsg("user", q);
      input.value = "";
      input.disabled = true; sendBtn.disabled = true;
      var typing = el("div", "ask-typing", "Steady is thinking…");
      body.appendChild(typing); scrollDown();

      fetch(API + "/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: q })
      })
        .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
        .then(function (r) {
          typing.remove();
          if (!r.ok) throw new Error(r.d.detail || "Something went wrong");
          addMsg("steady", r.d.answer || "Sorry, I didn't catch that — try rephrasing?");
        })
        .catch(function () {
          typing.remove();
          addMsg("err", "I couldn't reach the server just now. Please try again in a moment.");
        })
        .finally(function () {
          input.disabled = false; sendBtn.disabled = false; input.focus();
        });
    }

    fab.addEventListener("click", open);
    panel.querySelector(".ask-close").addEventListener("click", close);
    sendBtn.addEventListener("click", send);
    input.addEventListener("keydown", function (e) { if (e.key === "Enter") { e.preventDefault(); send(); } });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
