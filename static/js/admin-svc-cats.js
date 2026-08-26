(function () {
  function csrf() {
    var meta = document.querySelector('meta[name="csrf-token"]');
    return meta ? meta.getAttribute("content") || "" : "";
  }

  function saveOrder(list) {
    var kind = list.getAttribute("data-kind") || "main";
    var platform = list.getAttribute("data-platform") || "";
    var names = Array.prototype.map.call(list.querySelectorAll(".svc-cat-row[data-name]"), function (row) {
      return row.getAttribute("data-name");
    });
    if (!names.length) return;
    var body = new URLSearchParams();
    body.set("kind", kind);
    body.set("platform", platform);
    body.set("order", JSON.stringify(names));
    var tok = csrf();
    if (tok) body.set("_csrf", tok);
    list.classList.add("is-saving");
    fetch("/admin/services/sort", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
      },
      body: body.toString(),
      credentials: "same-origin",
    })
      .then(function (r) {
        return r.json().catch(function () {
          return { ok: false };
        });
      })
      .then(function (data) {
        list.classList.toggle("is-error", !(data && data.ok));
        if (data && data.ok) {
          list.classList.add("is-saved");
          setTimeout(function () {
            list.classList.remove("is-saved");
          }, 900);
        }
      })
      .catch(function () {
        list.classList.add("is-error");
      })
      .finally(function () {
        list.classList.remove("is-saving");
      });
  }

  function bindList(list) {
    if (!list) return;
    var dragRow = null;
    var moved = false;

    function clearDragState() {
      if (dragRow) {
        dragRow.classList.remove("is-dragging");
        dragRow.removeAttribute("data-drag-handle");
        dragRow.setAttribute("draggable", "false");
      }
      list.querySelectorAll(".svc-cat-row.is-over").forEach(function (el) {
        el.classList.remove("is-over");
      });
      dragRow = null;
      moved = false;
    }

    list.querySelectorAll(".svc-cat-row").forEach(function (row) {
      var handle = row.querySelector(".svc-drag");
      if (!handle) return;

      handle.addEventListener("mousedown", function (e) {
        if (e.button !== 0) return;
        row.setAttribute("data-drag-handle", "1");
        row.setAttribute("draggable", "true");
      });

      handle.addEventListener("mouseup", function () {
        if (!row.classList.contains("is-dragging")) {
          row.removeAttribute("data-drag-handle");
          row.setAttribute("draggable", "false");
        }
      });

      handle.addEventListener("mouseleave", function () {
        if (!row.classList.contains("is-dragging")) {
          row.removeAttribute("data-drag-handle");
          row.setAttribute("draggable", "false");
        }
      });

      handle.addEventListener("keydown", function (e) {
        if (e.key !== "Enter" && e.key !== " ") return;
        e.preventDefault();
        row.setAttribute("data-drag-handle", "1");
        row.setAttribute("draggable", "true");
      });
    });

    list.addEventListener("dragstart", function (e) {
      var row = e.target.closest(".svc-cat-row");
      if (!row || !list.contains(row) || row.getAttribute("data-drag-handle") !== "1") {
        e.preventDefault();
        return;
      }
      dragRow = row;
      moved = false;
      row.classList.add("is-dragging");
      e.dataTransfer.effectAllowed = "move";
      try {
        e.dataTransfer.setData("text/plain", row.getAttribute("data-name") || "");
      } catch (err) {}
      if (e.dataTransfer.setDragImage) {
        var ghost = row.cloneNode(true);
        ghost.style.width = row.offsetWidth + "px";
        ghost.style.opacity = "0.85";
        ghost.style.position = "absolute";
        ghost.style.top = "-9999px";
        ghost.style.left = "-9999px";
        document.body.appendChild(ghost);
        e.dataTransfer.setDragImage(ghost, 20, 20);
        setTimeout(function () {
          if (ghost.parentNode) ghost.parentNode.removeChild(ghost);
        }, 0);
      }
    });

    list.addEventListener("dragend", function () {
      if (dragRow && moved) saveOrder(list);
      clearDragState();
    });

    list.addEventListener("dragover", function (e) {
      if (!dragRow) return;
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      var row = e.target.closest(".svc-cat-row");
      if (!row || row === dragRow || !list.contains(row)) return;
      var rect = row.getBoundingClientRect();
      var before = e.clientY < rect.top + rect.height / 2;
      list.querySelectorAll(".svc-cat-row.is-over").forEach(function (el) {
        el.classList.remove("is-over");
      });
      row.classList.add("is-over");
      if (before) list.insertBefore(dragRow, row);
      else list.insertBefore(dragRow, row.nextSibling);
      moved = true;
    });

    list.addEventListener("drop", function (e) {
      e.preventDefault();
    });
  }

  bindList(document.getElementById("svc-mains-list"));
  bindList(document.getElementById("svc-subs-list"));
})();
