/* Steady Tasks board
   State-driven kanban over the Supabase tasks table.
   Depends on: @supabase/supabase-js (CDN) + config.js (SUPABASE_URL, SUPABASE_KEY)
*/
(function () {
  "use strict";

  var NEXT = { todo: "in_progress", in_progress: "done", done: "todo" };
  var COLUMNS = ["todo", "in_progress", "done"];
  var PRIORITY_RANK = { high: 0, medium: 1, low: 2 };
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var MODAL_FIELDS = ["title", "description", "priority", "category", "due_date"];

  var ICONS = {
    edit: '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/></svg>',
    archive: '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="4" rx="1"/><path d="M5 8v11a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8"/><path d="M10 12h4"/></svg>',
    restore: '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="4" rx="1"/><path d="M5 8v11a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8"/><path d="M12 17v-4"/><path d="M9.5 15.5 12 13l2.5 2.5"/></svg>',
    calendar: '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M8 3v4M16 3v4M3 10h18"/></svg>'
  };

  // --- DOM refs ------------------------------------------------------------
  var statusEl = document.getElementById("board-status");
  var boardEl = document.getElementById("board");
  var hintEl = document.getElementById("board-hint");
  var msgEl = document.getElementById("board-msg");
  var formEl = document.getElementById("task-form");
  var titleInput = document.getElementById("t-title");
  var descInput = document.getElementById("t-desc");
  var toolbarEl = document.getElementById("board-toolbar");
  var searchInput = document.getElementById("board-search");
  var archToggle = document.getElementById("show-archived");
  var overlayEl = document.getElementById("modal-overlay");
  var modalStatusEl = document.getElementById("modal-status");

  // --- State ---------------------------------------------------------------
  var tasks = new Map(); // id -> task row
  var state = {
    search: "",
    showArchived: false,
    sort: { todo: "created_at", in_progress: "created_at", done: "created_at" }
  };
  var popId = null;      // card to animate on next render
  var openTaskId = null; // task shown in the edit modal
  var live = false;      // realtime channel subscribed

  function setMsg(text, kind) {
    msgEl.textContent = text;
    msgEl.className = "form-msg " + (kind || "");
  }

  var client = null;
  try {
    client = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
  } catch (e) {
    console.error("Steady board: could not init Supabase", e);
  }
  if (!client) {
    statusEl.textContent = "Couldn't load the board.";
    setMsg("Supabase client failed to load — check your connection and config.js.", "err");
    return;
  }

  // --- Helpers ---------------------------------------------------------------
  function columnFor(status) {
    return boardEl.querySelector('.col[data-status="' + status + '"]');
  }

  function todayStr() {
    var d = new Date();
    return d.getFullYear() + "-" +
      String(d.getMonth() + 1).padStart(2, "0") + "-" +
      String(d.getDate()).padStart(2, "0");
  }

  function fmtDue(iso) {
    var p = String(iso).slice(0, 10).split("-"); // avoids Date() UTC-parsing offset
    return MONTHS[+p[1] - 1] + " " + (+p[2]);
  }

  function isOverdue(task) {
    return !!task.due_date &&
      task.status !== "done" &&
      String(task.due_date).slice(0, 10) < todayStr();
  }

  function matchesSearch(task) {
    if (!state.search) return true;
    var q = state.search.toLowerCase();
    return [task.title, task.description, task.category].some(function (v) {
      return v && String(v).toLowerCase().indexOf(q) !== -1;
    });
  }

  function sortTasks(list, key) {
    return list.slice().sort(function (a, b) {
      if (key === "priority") {
        var pa = PRIORITY_RANK[a.priority], pb = PRIORITY_RANK[b.priority];
        if (pa === undefined) pa = 1;
        if (pb === undefined) pb = 1;
        if (pa !== pb) return pa - pb;
      } else if (key === "due_date") {
        var da = a.due_date || "9999", db = b.due_date || "9999"; // no due date sorts last
        if (da !== db) return da < db ? -1 : 1;
      }
      return (a.created_at || "") < (b.created_at || "") ? -1 : 1;
    });
  }

  // --- Persistence -----------------------------------------------------------
  // Optimistically applies `patch` to the local task, re-renders, then persists.
  // Reverts and re-renders if Supabase rejects the update.
  function saveTask(task, patch, onError) {
    var prev = {};
    Object.keys(patch).forEach(function (k) { prev[k] = task[k]; task[k] = patch[k]; });
    render();

    return client.from("tasks").update(patch).eq("id", task.id).then(function (res) {
      if (res.error) {
        console.error("Steady board: update failed", res.error, patch);
        Object.keys(prev).forEach(function (k) { task[k] = prev[k]; });
        render();
        if (onError) onError(res.error);
        else setMsg("Couldn't save that change — please try again.", "err");
      }
      return res;
    });
  }

  // --- Rendering ---------------------------------------------------------------
  function render() {
    COLUMNS.forEach(function (status) {
      var col = columnFor(status);
      var cardsEl = col.querySelector(".cards");

      var list = [];
      tasks.forEach(function (t) {
        if (t.status !== status) return;
        if (t.archived && !state.showArchived) return;
        if (!matchesSearch(t)) return;
        list.push(t);
      });
      list = sortTasks(list, state.sort[status]);

      cardsEl.innerHTML = "";
      if (!list.length) {
        var empty = document.createElement("div");
        empty.className = "col-empty";
        empty.textContent = state.search ? "No matching tasks." : "No tasks here yet. Add one to get started.";
        cardsEl.appendChild(empty);
      } else {
        list.forEach(function (t) { cardsEl.appendChild(makeCard(t)); });
      }
      col.querySelector(".col-count").textContent = list.length;
    });

    var total = 0;
    tasks.forEach(function (t) { if (!t.archived) total++; });
    statusEl.textContent =
      (total === 1 ? "1 task on the board" : total + " tasks on the board") +
      (live ? " · syncing live" : "");

    if (popId) {
      var el = boardEl.querySelector('.card[data-id="' + popId + '"]');
      if (el) {
        el.classList.add("card-pop");
        el.addEventListener("animationend", function () { el.classList.remove("card-pop"); }, { once: true });
      }
      popId = null;
    }
  }

  function makeCard(task) {
    var card = document.createElement("div");
    card.className = "card" + (task.archived ? " is-archived" : "");
    card.setAttribute("role", "button");
    card.tabIndex = 0;
    card.draggable = true;
    card.dataset.id = task.id;

    // corner actions
    var actions = document.createElement("div");
    actions.className = "card-actions";

    var editBtn = document.createElement("button");
    editBtn.type = "button";
    editBtn.className = "card-action";
    editBtn.title = "Edit task";
    editBtn.setAttribute("aria-label", "Edit task");
    editBtn.innerHTML = ICONS.edit;
    editBtn.addEventListener("click", function (e) {
      e.stopPropagation();
      openModal(task);
    });
    actions.appendChild(editBtn);

    if (task.status === "done" || task.archived) {
      var archBtn = document.createElement("button");
      archBtn.type = "button";
      archBtn.className = "card-action";
      archBtn.title = task.archived ? "Restore" : "Archive";
      archBtn.setAttribute("aria-label", archBtn.title);
      archBtn.innerHTML = task.archived ? ICONS.restore : ICONS.archive;
      archBtn.addEventListener("click", function (e) {
        e.stopPropagation();
        saveTask(task, { archived: !task.archived });
      });
      actions.appendChild(archBtn);
    }
    card.appendChild(actions);

    var h = document.createElement("h3");
    var dot = document.createElement("span");
    dot.className = "dot-priority p-" + (PRIORITY_RANK.hasOwnProperty(task.priority) ? task.priority : "medium");
    h.appendChild(dot);
    h.appendChild(document.createTextNode((task.title || "Untitled").trim()));
    card.appendChild(h);

    if (task.description) {
      var p = document.createElement("p");
      p.textContent = task.description;
      card.appendChild(p);
    }

    if (task.category || task.due_date) {
      var meta = document.createElement("div");
      meta.className = "card-meta";
      if (task.category) {
        var chip = document.createElement("span");
        chip.className = "chip";
        chip.textContent = task.category;
        meta.appendChild(chip);
      }
      if (task.due_date) {
        var due = document.createElement("span");
        due.className = "due" + (isOverdue(task) ? " overdue" : "");
        due.innerHTML = ICONS.calendar;
        due.appendChild(document.createTextNode(" " + fmtDue(task.due_date) + (isOverdue(task) ? " · overdue" : "")));
        meta.appendChild(due);
      }
      card.appendChild(meta);
    }

    // drag
    var didDrag = false;
    card.addEventListener("dragstart", function (e) {
      didDrag = true;
      e.dataTransfer.setData("text/plain", task.id);
      e.dataTransfer.effectAllowed = "move";
      card.classList.add("is-dragging");
    });
    card.addEventListener("dragend", function () {
      card.classList.remove("is-dragging");
      setTimeout(function () { didDrag = false; }, 0);
    });

    // click card body = advance to next column; corner icons excluded
    card.addEventListener("click", function (e) {
      if (didDrag || e.target.closest(".card-action")) return;
      moveTask(task, NEXT[task.status]);
    });
    card.addEventListener("keydown", function (e) {
      if (e.target !== card) return; // let the corner icon buttons handle their own keys
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        moveTask(task, NEXT[task.status]);
      }
    });

    return card;
  }

  function moveTask(task, to) {
    if (!to || to === task.status) return;
    popId = task.id;
    setMsg("", "");
    saveTask(task, { status: to }, function () {
      setMsg("Couldn't move that card — please try again.", "err");
    });
  }

  // --- Edit modal ------------------------------------------------------------
  function modalInput(field) {
    return document.getElementById("m-" + field);
  }

  function setModalStatus(text, isErr) {
    modalStatusEl.textContent = text;
    modalStatusEl.className = "modal-status" + (isErr ? " err" : "");
  }

  function fillModal(task, skipFocused) {
    MODAL_FIELDS.forEach(function (field) {
      var input = modalInput(field);
      if (skipFocused && document.activeElement === input) return;
      var val = task[field];
      if (field === "due_date" && val) val = String(val).slice(0, 10);
      if (field === "priority") val = val || "medium";
      input.value = val || "";
    });
  }

  function openModal(task) {
    openTaskId = task.id;
    fillModal(task, false);
    setModalStatus("Changes save automatically", false);
    overlayEl.hidden = false;
    modalInput("title").focus();
  }

  function closeModal() {
    if (overlayEl.hidden) return;
    // flush any pending blur-save before hiding
    if (document.activeElement && overlayEl.contains(document.activeElement)) {
      document.activeElement.blur();
    }
    overlayEl.hidden = true;
    openTaskId = null;
  }

  function saveModalField(field) {
    var task = tasks.get(openTaskId);
    if (!task) return;

    var input = modalInput(field);
    var value = input.value.trim();

    if (field === "title" && !value) { input.value = task.title || ""; return; } // title can't be emptied
    if (field !== "priority" && !value) value = null;

    var current = task[field];
    if (field === "due_date" && current) current = String(current).slice(0, 10);
    if ((current || "") === (value || "")) return;

    var patch = {};
    patch[field] = value;
    setModalStatus("Saving…", false);
    saveTask(task, patch, function (error) {
      fillModal(task, true);
      setModalStatus("Couldn't save: " + error.message, true);
    }).then(function (res) {
      if (res && !res.error) setModalStatus("Saved ✓", false);
    });
  }

  MODAL_FIELDS.forEach(function (field) {
    var input = modalInput(field);
    input.addEventListener("blur", function () { saveModalField(field); });
    // selects and date pickers commit on change, often without a blur
    input.addEventListener("change", function () { saveModalField(field); });
  });

  document.getElementById("modal-close").addEventListener("click", closeModal);
  overlayEl.addEventListener("mousedown", function (e) {
    if (e.target === overlayEl) closeModal();
  });

  document.getElementById("modal-delete").addEventListener("click", function () {
    var task = tasks.get(openTaskId);
    if (!task) return;
    if (!window.confirm('Delete "' + (task.title || "this task") + '"? This can\'t be undone.')) return;

    client.from("tasks").delete().eq("id", task.id).select().then(function (res) {
      if (res.error || !res.data || !res.data.length) {
        console.error("Steady board: delete failed", res.error);
        setModalStatus(res.error ? "Couldn't delete: " + res.error.message
          : "Couldn't delete — the table may be missing a DELETE policy.", true);
        return;
      }
      tasks.delete(task.id);
      closeModal();
      render();
    });
  });

  // --- Board chrome ------------------------------------------------------------
  searchInput.addEventListener("input", function () {
    state.search = searchInput.value.trim();
    render();
  });

  archToggle.addEventListener("change", function () {
    state.showArchived = archToggle.checked;
    render();
  });

  boardEl.querySelectorAll(".col").forEach(function (col) {
    col.querySelector(".col-sort").addEventListener("change", function (e) {
      state.sort[col.dataset.status] = e.target.value;
      render();
    });

    col.addEventListener("dragover", function (e) {
      e.preventDefault(); // required to allow dropping
      e.dataTransfer.dropEffect = "move";
      col.classList.add("drag-over");
    });
    col.addEventListener("dragleave", function (e) {
      if (!col.contains(e.relatedTarget)) col.classList.remove("drag-over");
    });
    col.addEventListener("drop", function (e) {
      e.preventDefault();
      col.classList.remove("drag-over");
      var task = tasks.get(e.dataTransfer.getData("text/plain"));
      if (task) moveTask(task, col.dataset.status);
    });
  });

  // --- Add-task form ------------------------------------------------------------
  formEl.addEventListener("submit", function (e) {
    e.preventDefault();

    var btn = formEl.querySelector('button[type="submit"]');
    var title = titleInput.value.trim();
    if (!title) { titleInput.focus(); return; }

    var row = { title: title, description: descInput.value.trim() || null, status: "todo" };

    btn.disabled = true;
    btn.textContent = "Adding…";
    setMsg("", "");

    // .select() returns the inserted row so the card gets its real id
    client.from("tasks").insert(row).select().single().then(function (res) {
      btn.disabled = false;
      btn.textContent = "Add task";
      if (res.error) {
        console.error("Steady board: insert failed", res.error);
        setMsg("Couldn't add that task — please try again.", "err");
        return;
      }
      tasks.set(res.data.id, res.data);
      popId = res.data.id;
      render();
      formEl.reset();
      titleInput.focus();
    });
  });

  // --- Keyboard shortcuts ------------------------------------------------------
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { closeModal(); return; }
    if (e.key !== "n" && e.key !== "N") return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (!overlayEl.hidden) return;
    var t = e.target;
    if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.tagName === "SELECT" || t.isContentEditable)) return;
    e.preventDefault();
    titleInput.focus();
  });

  // --- Realtime sync -------------------------------------------------------------
  client
    .channel("tasks-realtime")
    .on("postgres_changes", { event: "*", schema: "public", table: "tasks" }, function (payload) {
      if (payload.eventType === "DELETE") {
        tasks.delete(payload.old.id);
        if (openTaskId === payload.old.id) closeModal();
      } else {
        tasks.set(payload.new.id, payload.new);
        if (openTaskId === payload.new.id) fillModal(payload.new, true);
      }
      render();
    })
    .subscribe(function (status) {
      if (status === "SUBSCRIBED") { live = true; render(); }
      if (status === "CHANNEL_ERROR" || status === "TIMED_OUT") { live = false; render(); }
    });

  // --- Initial load -----------------------------------------------------------
  client
    .from("tasks")
    .select("*")
    .order("created_at", { ascending: true })
    .then(function (res) {
      if (res.error) {
        console.error("Steady board: select failed", res.error);
        statusEl.textContent = "Couldn't load the board.";
        setMsg("Query failed: " + res.error.message, "err");
        return;
      }
      (res.data || []).forEach(function (t) { tasks.set(t.id, t); });
      render();
      formEl.hidden = false;
      toolbarEl.hidden = false;
      boardEl.hidden = false;
      hintEl.hidden = false;
      titleInput.focus();
    });
})();
