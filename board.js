/* Steady Tasks board
   State-driven kanban over the Supabase tasks table.
   Click a card to edit; drag to move between columns.
   Depends on: @supabase/supabase-js (CDN) + config.js (SUPABASE_URL, SUPABASE_KEY)
*/
(function () {
  "use strict";

  var COLUMNS = ["backlog", "todo", "in_progress", "done"];
  var PRIORITY_RANK = { high: 0, medium: 1, low: 2 };
  var MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var MODAL_FIELDS = ["title", "description", "priority", "category", "due_date", "owner"];
  var CAT_COLORS = 8; // .cat-0 … .cat-7 in board.html

  var ICONS = {
    archive: '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="4" rx="1"/><path d="M5 8v11a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8"/><path d="M10 12h4"/></svg>',
    restore: '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="4" rx="1"/><path d="M5 8v11a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V8"/><path d="M12 17v-4"/><path d="M9.5 15.5 12 13l2.5 2.5"/></svg>',
    clock: '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
    note: '<svg viewBox="0 0 24 24" width="12" height="12" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>'
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
  var filterRowEl = document.getElementById("filter-row");
  var overlayEl = document.getElementById("modal-overlay");
  var modalStatusEl = document.getElementById("modal-status");
  var notesListEl = document.getElementById("m-notes");
  var notesEmptyEl = document.getElementById("m-notes-empty");
  var noteInputEl = document.getElementById("m-note-input");
  var blockedToggle = document.getElementById("m-blocked");

  // --- State ---------------------------------------------------------------
  var tasks = new Map(); // id -> task row
  var state = {
    search: "",
    showArchived: false,
    sort: { backlog: "created_at", todo: "created_at", in_progress: "created_at", done: "created_at" },
    filters: { owner: new Set(), category: new Set(), priority: new Set(), blocked: false }
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

  function dateStr(d) {
    return d.getFullYear() + "-" +
      String(d.getMonth() + 1).padStart(2, "0") + "-" +
      String(d.getDate()).padStart(2, "0");
  }

  function todayStr() { return dateStr(new Date()); }

  function fmtDate(iso) {
    var p = String(iso).slice(0, 10).split("-"); // avoids Date() UTC-parsing offset
    return MONTHS[+p[1] - 1] + " " + (+p[2]);
  }

  function isOverdue(task) {
    return !!task.due_date &&
      task.status !== "done" &&
      String(task.due_date).slice(0, 10) < todayStr();
  }

  function catClass(name) {
    var hash = 0;
    for (var i = 0; i < name.length; i++) hash = (hash * 31 + name.charCodeAt(i)) % 997;
    return "cat-" + (hash % CAT_COLORS);
  }

  function initials(name) {
    var parts = name.trim().split(/\s+/).slice(0, 2);
    return parts.map(function (p) { return p[0]; }).join("").toUpperCase();
  }

  function taskNotes(task) {
    return Array.isArray(task.notes) ? task.notes : [];
  }

  function distinct(field) {
    var seen = new Set();
    tasks.forEach(function (t) {
      var v = t[field];
      if (v && String(v).trim()) seen.add(String(v).trim());
    });
    return Array.from(seen).sort();
  }

  function matchesSearch(task) {
    if (!state.search) return true;
    var q = state.search.toLowerCase();
    return [task.title, task.description, task.category, task.owner].some(function (v) {
      return v && String(v).toLowerCase().indexOf(q) !== -1;
    });
  }

  function matchesFilters(task) {
    var f = state.filters;
    if (f.blocked && !task.blocked) return false;
    if (f.owner.size && !f.owner.has(task.owner || "")) return false;
    if (f.category.size && !f.category.has(task.category || "")) return false;
    if (f.priority.size && !f.priority.has(task.priority || "medium")) return false;
    return true;
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
        if (!matchesSearch(t) || !matchesFilters(t)) return;
        list.push(t);
      });
      list = sortTasks(list, state.sort[status]);

      cardsEl.innerHTML = "";
      if (!list.length) {
        var empty = document.createElement("div");
        empty.className = "col-empty";
        empty.textContent = (state.search || filtersActive())
          ? "No matching tasks."
          : "No tasks here yet. Add one to get started.";
        cardsEl.appendChild(empty);
      } else {
        list.forEach(function (t) { cardsEl.appendChild(makeCard(t)); });
      }
      col.querySelector(".col-count").textContent = list.length;
    });

    renderStatusLine();
    renderFilters();
    renderDatalists();

    if (popId) {
      var el = boardEl.querySelector('.card[data-id="' + popId + '"]');
      if (el) {
        el.classList.add("card-pop");
        el.addEventListener("animationend", function () { el.classList.remove("card-pop"); }, { once: true });
      }
      popId = null;
    }
  }

  function filtersActive() {
    var f = state.filters;
    return f.blocked || f.owner.size || f.category.size || f.priority.size;
  }

  function renderStatusLine() {
    var total = 0, overdue = 0, blocked = 0;
    tasks.forEach(function (t) {
      if (t.archived) return;
      total++;
      if (isOverdue(t)) overdue++;
      if (t.blocked && t.status !== "done") blocked++;
    });

    statusEl.textContent = "";
    statusEl.appendChild(document.createTextNode(
      (total === 1 ? "1 task on the board" : total + " tasks on the board") +
      (live ? " · syncing live" : "")
    ));

    var alerts = [];
    if (overdue) alerts.push(overdue + " overdue");
    if (blocked) alerts.push(blocked + " blocked");
    if (alerts.length) {
      var span = document.createElement("span");
      span.className = "board-alert";
      span.textContent = " · " + alerts.join(" · ");
      statusEl.appendChild(span);
    }
  }

  function renderFilters() {
    filterRowEl.textContent = "";

    function addChip(label, isActive, onToggle) {
      var chip = document.createElement("button");
      chip.type = "button";
      chip.className = "filter-chip" + (isActive ? " active" : "");
      chip.textContent = label;
      chip.addEventListener("click", function () { onToggle(); render(); });
      filterRowEl.appendChild(chip);
    }

    function addSet(values, set) {
      values.forEach(function (v) {
        addChip(v, set.has(v), function () { set.has(v) ? set.delete(v) : set.add(v); });
      });
    }

    function addSep() {
      var sep = document.createElement("span");
      sep.className = "filter-sep";
      filterRowEl.appendChild(sep);
    }

    var label = document.createElement("span");
    label.className = "filter-label";
    label.textContent = "Filter";
    filterRowEl.appendChild(label);

    ["high", "medium", "low"].forEach(function (p) {
      addChip(p[0].toUpperCase() + p.slice(1), state.filters.priority.has(p), function () {
        state.filters.priority.has(p) ? state.filters.priority.delete(p) : state.filters.priority.add(p);
      });
    });

    var anyBlocked = false;
    tasks.forEach(function (t) { if (t.blocked && !t.archived) anyBlocked = true; });
    if (anyBlocked) {
      addChip("Blocked", state.filters.blocked, function () { state.filters.blocked = !state.filters.blocked; });
    }

    var owners = distinct("owner");
    if (owners.length) { addSep(); addSet(owners, state.filters.owner); }

    var cats = distinct("category");
    if (cats.length) { addSep(); addSet(cats, state.filters.category); }
  }

  function renderDatalists() {
    ["owner", "category"].forEach(function (field) {
      var dl = document.getElementById(field + "-list");
      dl.textContent = "";
      distinct(field).forEach(function (v) {
        var opt = document.createElement("option");
        opt.value = v;
        dl.appendChild(opt);
      });
    });
  }

  function makeCard(task) {
    var card = document.createElement("div");
    card.className = "card" +
      (task.archived ? " is-archived" : "") +
      (task.blocked ? " is-blocked" : "");
    card.setAttribute("role", "button");
    card.tabIndex = 0;
    card.draggable = true;
    card.dataset.id = task.id;

    // corner actions (archive only on Done / archived cards)
    if (task.status === "done" || task.archived) {
      var actions = document.createElement("div");
      actions.className = "card-actions";
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
      card.appendChild(actions);
    }

    // Trello-style label strips: category color, plus red for high priority
    if (task.category || task.priority === "high") {
      var strips = document.createElement("div");
      strips.className = "card-strips";
      if (task.priority === "high") {
        var pStrip = document.createElement("span");
        pStrip.className = "strip p-high";
        pStrip.title = "High priority";
        strips.appendChild(pStrip);
      }
      if (task.category) {
        var cStrip = document.createElement("span");
        cStrip.className = "strip " + catClass(task.category);
        cStrip.title = task.category;
        strips.appendChild(cStrip);
      }
      card.appendChild(strips);
    }

    var h = document.createElement("h3");
    h.textContent = (task.title || "Untitled").trim();
    card.appendChild(h);

    // description intentionally not shown on the card — open it to read
    var notes = taskNotes(task);
    if (task.due_date || task.owner || task.blocked || notes.length) {
      var meta = document.createElement("div");
      meta.className = "card-meta";
      if (task.blocked) {
        var flag = document.createElement("span");
        flag.className = "chip chip-blocked";
        flag.textContent = "Blocked";
        meta.appendChild(flag);
      }
      if (task.due_date) {
        var due = document.createElement("span");
        due.className = "due" + (isOverdue(task) ? " overdue" : "");
        due.innerHTML = ICONS.clock;
        due.appendChild(document.createTextNode(" " + fmtDate(task.due_date)));
        meta.appendChild(due);
      }
      if (notes.length) {
        var nc = document.createElement("span");
        nc.className = "note-count";
        nc.title = notes.length + (notes.length === 1 ? " note" : " notes");
        nc.innerHTML = ICONS.note;
        nc.appendChild(document.createTextNode(" " + notes.length));
        meta.appendChild(nc);
      }
      if (task.owner) {
        var av = document.createElement("span");
        av.className = "owner-avatar";
        av.title = task.owner;
        av.textContent = initials(task.owner);
        meta.appendChild(av);
      }
      card.appendChild(meta);
    }

    // drag to move
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

    // click (or Enter/Space) opens the edit modal; corner icons excluded
    card.addEventListener("click", function (e) {
      if (didDrag || e.target.closest(".card-action")) return;
      openModal(task);
    });
    card.addEventListener("keydown", function (e) {
      if (e.target !== card) return; // let the corner icon buttons handle their own keys
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        openModal(task);
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
    var statusSel = modalInput("status");
    if (!(skipFocused && document.activeElement === statusSel)) {
      statusSel.value = COLUMNS.indexOf(task.status) !== -1 ? task.status : "todo";
    }
    var avatar = document.getElementById("m-owner-avatar");
    avatar.hidden = !task.owner;
    avatar.textContent = task.owner ? initials(task.owner) : "";
    avatar.title = task.owner || "";
    blockedToggle.checked = !!task.blocked;
    renderNotes(task);
  }

  function renderNotes(task) {
    var notes = taskNotes(task);
    notesListEl.textContent = "";
    notesEmptyEl.hidden = !!notes.length;
    // newest first, like Trello's activity feed; idx stays the index in the stored array
    var ordered = notes.map(function (note, idx) { return { note: note, idx: idx }; }).reverse();
    ordered.forEach(function (entry) {
      var note = entry.note, idx = entry.idx;
      var li = document.createElement("li");
      var date = document.createElement("span");
      date.className = "note-date";
      date.textContent = note.at ? fmtDate(note.at) : "";
      var text = document.createElement("span");
      text.className = "note-text";
      text.textContent = note.text || "";
      var del = document.createElement("button");
      del.type = "button";
      del.className = "note-del";
      del.title = "Delete note";
      del.setAttribute("aria-label", "Delete note");
      del.textContent = "×";
      del.addEventListener("click", function () {
        var next = taskNotes(task).slice();
        next.splice(idx, 1);
        setModalStatus("Saving…", false);
        saveTask(task, { notes: next }, function (error) {
          renderNotes(task);
          setModalStatus("Couldn't save: " + error.message, true);
        }).then(function (res) {
          if (res && !res.error) { renderNotes(task); setModalStatus("Saved ✓", false); }
        });
      });
      li.appendChild(date);
      li.appendChild(text);
      li.appendChild(del);
      notesListEl.appendChild(li);
    });
  }

  function addNote() {
    var task = tasks.get(openTaskId);
    if (!task) return;
    var text = noteInputEl.value.trim();
    if (!text) { noteInputEl.focus(); return; }

    var next = taskNotes(task).slice();
    next.push({ text: text, at: new Date().toISOString() });
    setModalStatus("Saving…", false);
    saveTask(task, { notes: next }, function (error) {
      renderNotes(task);
      setModalStatus("Couldn't save: " + error.message, true);
    }).then(function (res) {
      if (res && !res.error) {
        noteInputEl.value = "";
        renderNotes(task);
        setModalStatus("Saved ✓", false);
        noteInputEl.focus();
      }
    });
  }

  function openModal(task) {
    openTaskId = task.id;
    fillModal(task, false);
    noteInputEl.value = "";
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
      if (res && !res.error) {
        setModalStatus("Saved ✓", false);
        if (field === "owner") {
          var avatar = document.getElementById("m-owner-avatar");
          avatar.hidden = !task.owner;
          avatar.textContent = task.owner ? initials(task.owner) : "";
          avatar.title = task.owner || "";
        }
      }
    });
  }

  // status chip in the modal header moves the card between columns
  modalInput("status").addEventListener("change", function () {
    var task = tasks.get(openTaskId);
    if (!task || this.value === task.status) return;
    setModalStatus("Saving…", false);
    var sel = this;
    saveTask(task, { status: sel.value }, function (error) {
      sel.value = task.status;
      setModalStatus("Couldn't save: " + error.message, true);
    }).then(function (res) {
      if (res && !res.error) setModalStatus("Saved ✓", false);
    });
  });

  MODAL_FIELDS.forEach(function (field) {
    var input = modalInput(field);
    input.addEventListener("blur", function () { saveModalField(field); });
    // selects and date pickers commit on change, often without a blur
    input.addEventListener("change", function () { saveModalField(field); });
  });

  blockedToggle.addEventListener("change", function () {
    var task = tasks.get(openTaskId);
    if (!task) return;
    setModalStatus("Saving…", false);
    saveTask(task, { blocked: blockedToggle.checked }, function (error) {
      blockedToggle.checked = !!task.blocked;
      setModalStatus("Couldn't save: " + error.message, true);
    }).then(function (res) {
      if (res && !res.error) setModalStatus("Saved ✓", false);
    });
  });

  document.querySelectorAll(".quick-due button").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var input = modalInput("due_date");
      if (btn.dataset.days === "clear") {
        input.value = "";
      } else {
        var d = new Date();
        d.setDate(d.getDate() + parseInt(btn.dataset.days, 10));
        input.value = dateStr(d);
      }
      saveModalField("due_date");
    });
  });

  document.getElementById("m-note-add").addEventListener("click", addNote);
  noteInputEl.addEventListener("keydown", function (e) {
    if (e.key === "Enter") { e.preventDefault(); addNote(); }
  });

  document.getElementById("modal-close").addEventListener("click", closeModal);
  document.getElementById("modal-done").addEventListener("click", closeModal);
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

    // Trello-style "+ Add a card" at the foot of each column
    var addBtn = col.querySelector(".col-add");
    var addForm = col.querySelector(".col-add-form");
    var addInput = addForm.querySelector("input");

    function closeQuickAdd() {
      addForm.hidden = true;
      addBtn.hidden = false;
      addInput.value = "";
    }

    addBtn.addEventListener("click", function () {
      addBtn.hidden = true;
      addForm.hidden = false;
      addInput.focus();
    });
    addInput.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { e.stopPropagation(); closeQuickAdd(); }
    });
    addInput.addEventListener("blur", function () {
      if (!addInput.value.trim()) closeQuickAdd();
    });
    addForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var title = addInput.value.trim();
      if (!title) { closeQuickAdd(); return; }
      client.from("tasks").insert({ title: title, status: col.dataset.status }).select().single().then(function (res) {
        if (res.error) {
          console.error("Steady board: insert failed", res.error);
          setMsg("Couldn't add that task — please try again.", "err");
          return;
        }
        tasks.set(res.data.id, res.data);
        popId = res.data.id;
        render();
        addInput.value = "";
        addInput.focus(); // keep adding
      });
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
      filterRowEl.hidden = false;
      boardEl.hidden = false;
      hintEl.hidden = false;
      titleInput.focus();
    });
})();
