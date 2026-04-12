const shell = document.querySelector(".app-shell");

if (shell) {
  const config = JSON.parse(shell.dataset.config);
  const treeRoot = document.getElementById("tree-root");
  const newFileButton = document.getElementById("new-file");
  const newDirectoryButton = document.getElementById("new-directory");
  const refreshButton = document.getElementById("refresh-tree");
  const decreaseFontSizeButton = document.getElementById("decrease-font-size");
  const increaseFontSizeButton = document.getElementById("increase-font-size");
  const fontSizeLabel = document.getElementById("font-size-label");
  const saveButton = document.getElementById("save-button");
  const openSettingsButton = document.getElementById("open-settings");
  const closeSettingsButton = document.getElementById("close-settings");
  const cancelSettingsButton = document.getElementById("cancel-settings");
  const saveSettingsButton = document.getElementById("save-settings");
  const settingsModal = document.getElementById("settings-modal");
  const browseContentRootButton = document.getElementById("browse-content-root");
  const directoryBrowserModal = document.getElementById("directory-browser-modal");
  const closeDirectoryBrowserButton = document.getElementById("close-directory-browser");
  const cancelDirectoryBrowserButton = document.getElementById("cancel-directory-browser");
  const directoryBrowserCurrentPath = document.getElementById("directory-browser-current-path");
  const directoryBrowserList = document.getElementById("directory-browser-list");
  const directoryBrowserUpButton = document.getElementById("directory-browser-up");
  const directoryBrowserSelectButton = document.getElementById("directory-browser-select");
  const createModal = document.getElementById("create-modal");
  const closeCreateButton = document.getElementById("close-create");
  const cancelCreateButton = document.getElementById("cancel-create");
  const confirmCreateButton = document.getElementById("confirm-create");
  const createNameInput = document.getElementById("create-name-input");
  const createParentLabel = document.getElementById("create-parent-label");
  const createTitle = document.getElementById("create-title");
  const createHint = document.getElementById("create-hint");
  const contentRootInput = document.getElementById("content-root-input");
  const sortModeSelect = document.getElementById("sort-mode-select");
  const themeModeSelect = document.getElementById("theme-mode-select");
  const editorFontSizeInput = document.getElementById("editor-font-size-input");
  const contentRootDisplay = document.getElementById("content-root-display");
  const currentFileLabel = document.getElementById("current-file-label");
  const currentFilePath = document.getElementById("current-file-path");
  const statusMessage = document.getElementById("status-message");
  const emptyState = document.getElementById("empty-state");
  const unsupportedState = document.getElementById("unsupported-state");

  const expandedDirectories = new Set([""]);
  let treeData = null;
  let preferences = null;
  let selectedPath = null;
  let selectedEditable = false;
  let selectedTreePath = "";
  let selectedTreeKind = "directory";
  let dragState = null;
  let createKind = "file";
  let directoryBrowserState = null;

  const editor = new toastui.Editor({
    el: document.getElementById("editor"),
    height: "100%",
    initialEditType: "wysiwyg",
    previewStyle: "vertical",
    initialValue: "",
    usageStatistics: false,
    hideModeSwitch: false,
    autofocus: false,
  });

  function clampFontSize(value) {
    return Math.max(12, Math.min(28, Number.parseInt(value, 10) || 16));
  }

  function applyTheme(themeMode) {
    document.body.dataset.theme = themeMode;
    shell.dataset.themeMode = themeMode;
  }

  function applyEditorFontSize(fontSize) {
    const normalized = clampFontSize(fontSize);
    document.documentElement.style.setProperty("--editor-font-size", `${normalized}px`);
    shell.dataset.editorFontSize = String(normalized);
    fontSizeLabel.textContent = `${normalized}px`;
    editorFontSizeInput.value = String(normalized);
  }

  function openSettingsModal() {
    settingsModal.classList.remove("hidden");
    settingsModal.setAttribute("aria-hidden", "false");
  }

  function closeSettingsModal() {
    settingsModal.classList.add("hidden");
    settingsModal.setAttribute("aria-hidden", "true");
    closeDirectoryBrowserModal();
  }

  function openDirectoryBrowserModal() {
    directoryBrowserModal.classList.remove("hidden");
    directoryBrowserModal.setAttribute("aria-hidden", "false");
  }

  function closeDirectoryBrowserModal() {
    directoryBrowserModal.classList.add("hidden");
    directoryBrowserModal.setAttribute("aria-hidden", "true");
  }

  function getCurrentParentPath() {
    if (!selectedTreePath) {
      return "";
    }
    return selectedTreeKind === "directory" ? selectedTreePath : getParentPath(selectedTreePath);
  }

  function openCreateModal(kind) {
    createKind = kind;
    const parentPath = getCurrentParentPath();
    createTitle.textContent = kind === "directory" ? "Nowy katalog" : "Nowy plik";
    createHint.textContent =
      kind === "directory"
        ? "Katalog zostanie utworzony w wybranej lokalizacji."
        : "Dla pliku rozszerzenie `.md` zostanie dodane automatycznie, jesli go nie podasz.";
    createParentLabel.textContent = `Lokalizacja: ${parentPath || "katalog glowny"}`;
    createNameInput.value = "";
    createModal.classList.remove("hidden");
    createModal.setAttribute("aria-hidden", "false");
    window.setTimeout(() => createNameInput.focus(), 0);
  }

  function closeCreateModal() {
    createModal.classList.add("hidden");
    createModal.setAttribute("aria-hidden", "true");
  }

  function setStatus(message, isError = false) {
    statusMessage.textContent = message;
    statusMessage.style.color = isError ? "#9a3412" : "";
  }

  function toggleOverlay({ empty = false, unsupported = false }) {
    emptyState.classList.toggle("hidden", !empty);
    unsupportedState.classList.toggle("hidden", !unsupported);
  }

  function updateHeader(name, path) {
    currentFileLabel.textContent = name || "Wybierz notatke Markdown";
    currentFilePath.textContent = path || "Brak zaznaczonego pliku.";
  }

  function openParentDirectories(path) {
    const parts = path.split("/");
    let current = "";
    for (let index = 0; index < parts.length - 1; index += 1) {
      current = current ? `${current}/${parts[index]}` : parts[index];
      expandedDirectories.add(current);
    }
  }

  async function requestJson(url, options = {}) {
    const response = await fetch(url, {
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
      },
      ...options,
    });

    if (response.status === 401) {
      window.location.href = "/login";
      throw new Error("Unauthorized");
    }

    if (!response.ok) {
      let detail = "Wystapil blad.";
      try {
        const payload = await response.json();
        detail = payload.detail || detail;
      } catch (error) {
        detail = response.statusText || detail;
      }
      throw new Error(detail);
    }

    return response.json();
  }

  function findFirstEditable(node) {
    if (node.kind === "file" && node.editable) {
      return node.path;
    }

    if (node.children) {
      for (const child of node.children) {
        const result = findFirstEditable(child);
        if (result) {
          return result;
        }
      }
    }

    return null;
  }

  async function loadPreferences() {
    preferences = await requestJson(config.preferencesUrl, { method: "GET" });
    contentRootInput.value = preferences.content_root;
    sortModeSelect.value = preferences.sort_mode;
    themeModeSelect.value = preferences.theme_mode;
    editorFontSizeInput.value = String(preferences.editor_font_size);
    contentRootDisplay.textContent = preferences.content_root;
    applyTheme(preferences.theme_mode);
    applyEditorFontSize(preferences.editor_font_size);
  }

  async function persistPreferences(overrides = {}) {
    const payload = {
      content_root: contentRootInput.value,
      sort_mode: sortModeSelect.value,
      theme_mode: themeModeSelect.value,
      editor_font_size: clampFontSize(editorFontSizeInput.value),
      ...overrides,
    };
    preferences = await requestJson(config.preferencesUrl, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    contentRootDisplay.textContent = preferences.content_root;
    applyTheme(preferences.theme_mode);
    applyEditorFontSize(preferences.editor_font_size);
    return preferences;
  }

  function getParentPath(path) {
    const parts = path.split("/");
    return parts.length > 1 ? parts.slice(0, -1).join("/") : "";
  }

  function renderDirectoryBrowser(payload) {
    directoryBrowserState = payload;
    directoryBrowserCurrentPath.textContent = payload.current_path;
    directoryBrowserList.innerHTML = "";
    directoryBrowserUpButton.disabled = !payload.parent_path;

    if (!payload.directories.length) {
      const empty = document.createElement("div");
      empty.className = "directory-browser-empty muted";
      empty.textContent = "Brak podkatalogow w tej lokalizacji.";
      directoryBrowserList.appendChild(empty);
      return;
    }

    payload.directories.forEach((directory) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "directory-browser-item";
      button.innerHTML = `
        <span class="directory-browser-item-name">${directory.name}</span>
        <span class="directory-browser-item-path">${directory.path}</span>
      `;
      button.addEventListener("click", () => {
        loadDirectoryBrowser(directory.path);
      });
      directoryBrowserList.appendChild(button);
    });
  }

  async function loadDirectoryBrowser(path = "") {
    const query = path ? `?path=${encodeURIComponent(path)}` : "";
    const payload = await requestJson(`${config.directoriesUrl}${query}`, { method: "GET" });
    renderDirectoryBrowser(payload);
  }

  async function openDirectoryBrowser() {
    try {
      setStatus("Wczytuje katalogi...");
      openDirectoryBrowserModal();
      const startPath = contentRootInput.value.trim();
      await loadDirectoryBrowser(startPath);
      setStatus("Mozesz wybrac katalog.");
    } catch (error) {
      closeDirectoryBrowserModal();
      setStatus(error.message, true);
    }
  }

  function selectDirectoryFromBrowser() {
    if (!directoryBrowserState) {
      return;
    }
    contentRootInput.value = directoryBrowserState.current_path;
    closeDirectoryBrowserModal();
    setStatus("Katalog wybrany. Zapisz ustawienia, aby go zastosowac.");
    contentRootInput.focus();
    contentRootInput.setSelectionRange(contentRootInput.value.length, contentRootInput.value.length);
  }

  function findDirectoryNode(node, targetPath) {
    if (node.kind === "directory" && node.path === targetPath) {
      return node;
    }

    if (!node.children) {
      return null;
    }

    for (const child of node.children) {
      if (child.kind !== "directory") {
        continue;
      }
      const match = findDirectoryNode(child, targetPath);
      if (match) {
        return match;
      }
    }

    return null;
  }

  function enableDragAndDrop(row, node) {
    if (!node.path) {
      return;
    }

    row.draggable = true;
    row.classList.add("is-draggable");

    row.addEventListener("dragstart", (event) => {
      dragState = {
        path: node.path,
        parentPath: getParentPath(node.path),
        kind: node.kind,
      };
      row.classList.add("is-dragging");
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", node.path);
    });

    row.addEventListener("dragend", () => {
      row.classList.remove("is-dragging");
      row.classList.remove("is-drop-target");
      dragState = null;
      treeRoot.classList.remove("is-drop-target-root");
      document.querySelectorAll(".tree-row.is-drop-target").forEach((element) => {
        element.classList.remove("is-drop-target");
      });
    });

    row.addEventListener("dragover", (event) => {
      if (!dragState || dragState.path === node.path) {
        return;
      }
      if (node.kind === "directory") {
        if (dragState.kind === "directory" && node.path.startsWith(`${dragState.path}/`)) {
          return;
        }
      } else if (
        preferences?.sort_mode !== "manual" ||
        dragState.parentPath !== getParentPath(node.path)
      ) {
        return;
      }
      event.preventDefault();
      event.dataTransfer.dropEffect = "move";
      row.classList.add("is-drop-target");
    });

    row.addEventListener("dragleave", () => {
      row.classList.remove("is-drop-target");
    });

    row.addEventListener("drop", async (event) => {
      if (!dragState || dragState.path === node.path) {
        return;
      }
      event.preventDefault();
      row.classList.remove("is-drop-target");
      if (node.kind === "directory") {
        if (dragState.kind === "directory" && node.path.startsWith(`${dragState.path}/`)) {
          return;
        }
        await moveItemToDirectory(dragState.path, node.path);
        return;
      }

      if (
        preferences?.sort_mode === "manual" &&
        dragState.parentPath === getParentPath(node.path)
      ) {
        await reorderWithinParent(dragState.path, node.path, dragState.parentPath);
      }
    });
  }

  function renderNode(node) {
    const listItem = document.createElement("li");
    listItem.className = "tree-item";

    const row = document.createElement("div");
    row.className = "tree-row";

    if (node.kind === "directory") {
      const toggle = document.createElement("button");
      toggle.type = "button";
      toggle.className = "tree-toggle";
      const isExpanded = expandedDirectories.has(node.path);
      toggle.textContent = isExpanded ? "▾" : "▸";
      toggle.addEventListener("click", () => {
        if (expandedDirectories.has(node.path)) {
          expandedDirectories.delete(node.path);
        } else {
          expandedDirectories.add(node.path);
        }
        renderTree(treeData);
      });
      row.appendChild(toggle);

      const label = document.createElement("button");
      label.type = "button";
      label.className = "tree-link";
      label.textContent = node.name;
      if (selectedTreePath === node.path) {
        label.classList.add("is-active");
      }
      label.addEventListener("click", () => {
        selectedTreePath = node.path;
        selectedTreeKind = "directory";
        if (expandedDirectories.has(node.path)) {
          expandedDirectories.delete(node.path);
        } else {
          expandedDirectories.add(node.path);
        }
        renderTree(treeData);
      });
      row.appendChild(label);
      enableDragAndDrop(row, node);
      listItem.appendChild(row);

      if (isExpanded && node.children.length) {
        const childList = document.createElement("ul");
        childList.className = "tree-list";
        node.children.forEach((child) => childList.appendChild(renderNode(child)));
        listItem.appendChild(childList);
      }

      return listItem;
    }

    const spacer = document.createElement("span");
    spacer.className = "tree-toggle";
    spacer.textContent = "·";
    row.appendChild(spacer);

    const fileButton = document.createElement("button");
    fileButton.type = "button";
    fileButton.className = "tree-link";
    fileButton.textContent = node.name;
    if (selectedTreePath === node.path) {
      fileButton.classList.add("is-active");
    }
    if (!node.editable) {
      fileButton.classList.add("is-disabled");
    }
    fileButton.addEventListener("click", () => {
      selectedTreePath = node.path;
      selectedTreeKind = "file";
      loadFile(node.path);
    });
    row.appendChild(fileButton);
    enableDragAndDrop(row, node);
    listItem.appendChild(row);

    return listItem;
  }

  function renderTree(node) {
    treeRoot.innerHTML = "";
    if (!node) {
      return;
    }

    const list = document.createElement("ul");
    list.className = "tree-list tree-list-root";
    node.children.forEach((child) => list.appendChild(renderNode(child)));
    treeRoot.appendChild(list);
  }

  async function loadTree({ autoSelect = false } = {}) {
    setStatus("Odswiezam drzewo plikow...");
    treeData = await requestJson(config.treeUrl, { method: "GET" });
    renderTree(treeData);
    setStatus("Drzewo plikow gotowe.");

    if (autoSelect && !selectedPath) {
      const firstEditable = findFirstEditable(treeData);
      if (firstEditable) {
        await loadFile(firstEditable);
      }
    }
  }

  async function loadFile(path) {
    try {
      setStatus("Wczytuje plik...");
      const file = await requestJson(`${config.fileUrl}?path=${encodeURIComponent(path)}`, {
        method: "GET",
      });

      selectedPath = file.path;
      selectedEditable = file.editable;
      selectedTreePath = file.path;
      selectedTreeKind = "file";
      openParentDirectories(file.path);
      updateHeader(file.name, file.path);
      saveButton.disabled = !file.editable;

      if (file.editable) {
        editor.setMarkdown(file.content || "", false);
        toggleOverlay({ empty: false, unsupported: false });
        setStatus("Plik gotowy do edycji.");
      } else {
        editor.setMarkdown("", false);
        toggleOverlay({ empty: false, unsupported: true });
        setStatus(file.message || "Tego pliku nie mozna edytowac.");
      }

      renderTree(treeData);
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  async function saveFile() {
    if (!selectedPath || !selectedEditable) {
      return;
    }

    try {
      setStatus("Zapisuje plik...");
      await requestJson(config.saveUrl, {
        method: "PUT",
        body: JSON.stringify({
          path: selectedPath,
          content: editor.getMarkdown(),
        }),
      });
      toggleOverlay({ empty: false, unsupported: false });
      setStatus("Zmiany zapisane.");
      await loadTree();
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  async function saveSettings() {
    try {
      setStatus("Zapisuje ustawienia...");
      await persistPreferences();
      selectedPath = null;
      selectedEditable = false;
      saveButton.disabled = true;
      updateHeader("", "");
      editor.setMarkdown("", false);
      toggleOverlay({ empty: true, unsupported: false });
      closeSettingsModal();
      await loadTree({ autoSelect: true });
      setStatus("Ustawienia zapisane.");
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  async function adjustEditorFontSize(delta) {
    const nextSize = clampFontSize((preferences?.editor_font_size || 16) + delta);
    try {
      setStatus("Aktualizuje rozmiar czcionki...");
      await persistPreferences({ editor_font_size: nextSize });
      setStatus("Rozmiar czcionki zapisany.");
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  async function createItem() {
    const parentPath = getCurrentParentPath();
    const name = createNameInput.value.trim();
    if (!name) {
      setStatus("Podaj nazwe nowego elementu.", true);
      createNameInput.focus();
      return;
    }

    try {
      setStatus("Tworze nowy element...");
      const created = await requestJson(config.createUrl, {
        method: "POST",
        body: JSON.stringify({
          parent_path: parentPath,
          name,
          kind: createKind,
        }),
      });
      if (parentPath) {
        expandedDirectories.add(parentPath);
      }
      closeCreateModal();
      await loadTree();
      selectedTreePath = created.path;
      selectedTreeKind = created.kind;
      if (created.kind === "file") {
        await loadFile(created.path);
      } else {
        expandedDirectories.add(created.path);
        renderTree(treeData);
        setStatus("Katalog utworzony.");
      }
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  async function moveItemToDirectory(sourcePath, targetParentPath) {
    if (getParentPath(sourcePath) === targetParentPath) {
      return;
    }

    try {
      setStatus("Przenosze element...");
      const moved = await requestJson(config.moveUrl, {
        method: "PUT",
        body: JSON.stringify({
          source_path: sourcePath,
          target_parent_path: targetParentPath,
        }),
      });
      expandedDirectories.add(targetParentPath);
      if (moved.kind === "directory") {
        expandedDirectories.add(moved.path);
      }
      await loadTree();
      selectedTreePath = moved.path;
      selectedTreeKind = moved.kind;
      if (moved.kind === "file") {
        await loadFile(moved.path);
      } else {
        renderTree(treeData);
        setStatus("Element przeniesiony.");
      }
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  async function reorderWithinParent(sourcePath, targetPath, parentPath) {
    const parentNode = parentPath ? findDirectoryNode(treeData, parentPath) : treeData;
    if (!parentNode || !parentNode.children) {
      return;
    }

    const orderedPaths = parentNode.children.map((child) => child.path);
    const sourceIndex = orderedPaths.indexOf(sourcePath);
    const targetIndex = orderedPaths.indexOf(targetPath);
    if (sourceIndex === -1 || targetIndex === -1 || sourceIndex === targetIndex) {
      return;
    }

    const [moved] = orderedPaths.splice(sourceIndex, 1);
    orderedPaths.splice(targetIndex, 0, moved);

    try {
      setStatus("Aktualizuje manualny order...");
      preferences = await requestJson(config.orderUrl, {
        method: "PUT",
        body: JSON.stringify({
          parent_path: parentPath,
          ordered_paths: orderedPaths,
        }),
      });
      await loadTree();
      setStatus("Order zapisany.");
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  refreshButton.addEventListener("click", () => {
    loadTree();
  });

  treeRoot.addEventListener("dragover", (event) => {
    if (!dragState || !dragState.parentPath) {
      return;
    }
    if (event.target.closest(".tree-row")) {
      return;
    }
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
    treeRoot.classList.add("is-drop-target-root");
  });

  treeRoot.addEventListener("dragleave", (event) => {
    if (event.target === treeRoot) {
      treeRoot.classList.remove("is-drop-target-root");
    }
  });

  treeRoot.addEventListener("drop", async (event) => {
    if (!dragState || !dragState.parentPath) {
      return;
    }
    if (event.target.closest(".tree-row")) {
      return;
    }
    event.preventDefault();
    treeRoot.classList.remove("is-drop-target-root");
    await moveItemToDirectory(dragState.path, "");
  });

  decreaseFontSizeButton.addEventListener("click", () => adjustEditorFontSize(-1));
  increaseFontSizeButton.addEventListener("click", () => adjustEditorFontSize(1));
  newFileButton.addEventListener("click", () => openCreateModal("file"));
  newDirectoryButton.addEventListener("click", () => openCreateModal("directory"));
  openSettingsButton.addEventListener("click", openSettingsModal);
  closeSettingsButton.addEventListener("click", closeSettingsModal);
  cancelSettingsButton.addEventListener("click", closeSettingsModal);
  browseContentRootButton.addEventListener("click", openDirectoryBrowser);
  closeDirectoryBrowserButton.addEventListener("click", closeDirectoryBrowserModal);
  cancelDirectoryBrowserButton.addEventListener("click", closeDirectoryBrowserModal);
  directoryBrowserUpButton.addEventListener("click", async () => {
    if (!directoryBrowserState?.parent_path) {
      return;
    }
    try {
      await loadDirectoryBrowser(directoryBrowserState.parent_path);
    } catch (error) {
      setStatus(error.message, true);
    }
  });
  directoryBrowserSelectButton.addEventListener("click", selectDirectoryFromBrowser);
  settingsModal.addEventListener("click", (event) => {
    if (event.target === settingsModal) {
      closeSettingsModal();
    }
  });
  directoryBrowserModal.addEventListener("click", (event) => {
    if (event.target === directoryBrowserModal) {
      closeDirectoryBrowserModal();
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !directoryBrowserModal.classList.contains("hidden")) {
      closeDirectoryBrowserModal();
      return;
    }
    if (event.key === "Escape" && !settingsModal.classList.contains("hidden")) {
      closeSettingsModal();
    }
    if (event.key === "Escape" && !createModal.classList.contains("hidden")) {
      closeCreateModal();
    }
    if (event.key === "Enter" && document.activeElement === createNameInput && !createModal.classList.contains("hidden")) {
      createItem();
    }
  });
  closeCreateButton.addEventListener("click", closeCreateModal);
  cancelCreateButton.addEventListener("click", closeCreateModal);
  confirmCreateButton.addEventListener("click", createItem);
  createModal.addEventListener("click", (event) => {
    if (event.target === createModal) {
      closeCreateModal();
    }
  });
  saveButton.addEventListener("click", saveFile);
  saveSettingsButton.addEventListener("click", saveSettings);

  applyTheme(shell.dataset.themeMode || "light");
  applyEditorFontSize(shell.dataset.editorFontSize || "16");
  toggleOverlay({ empty: true, unsupported: false });
  loadPreferences()
    .then(() => loadTree({ autoSelect: true }))
    .catch((error) => setStatus(error.message, true));
}
