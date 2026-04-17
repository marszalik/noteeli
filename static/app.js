const shell = document.querySelector(".app-shell");

if (shell) {
  const config = JSON.parse(shell.dataset.config);
  const treeRoot = document.getElementById("tree-root");
  const newFileButton = document.getElementById("new-file");
  const newDirectoryButton = document.getElementById("new-directory");
  const refreshButton = document.getElementById("refresh-tree");
  const resetTreeRootButton = document.getElementById("reset-tree-root");
  const toggleHiddenFilesButton = document.getElementById("toggle-hidden-files");
  const decreaseFontSizeButton = document.getElementById("decrease-font-size");
  const increaseFontSizeButton = document.getElementById("increase-font-size");
  const fontSizeLabel = document.getElementById("font-size-label");
  const saveButton = document.getElementById("save-button");
  const editorModeToggle = document.getElementById("editor-mode-toggle");
  const togglePreferenceProfilesButton = document.getElementById("toggle-preference-profiles");
  const preferenceProfilesDropdown = document.getElementById("preference-profiles-dropdown");
  const preferenceProfilesList = document.getElementById("preference-profiles-list");
  const openSettingsButton = document.getElementById("open-settings");
  const closeSettingsButton = document.getElementById("close-settings");
  const cancelSettingsButton = document.getElementById("cancel-settings");
  const saveSettingsButton = document.getElementById("save-settings");
  const saveProfileButton = document.getElementById("save-profile");
  const cancelProfileEditButton = document.getElementById("cancel-profile-edit");
  const settingsModal = document.getElementById("settings-modal");
  const browseContentRootButton = document.getElementById("browse-content-root");
  const directoryBrowserModal = document.getElementById("directory-browser-modal");
  const closeDirectoryBrowserButton = document.getElementById("close-directory-browser");
  const cancelDirectoryBrowserButton = document.getElementById("cancel-directory-browser");
  const directoryBrowserCurrentPath = document.getElementById("directory-browser-current-path");
  const directoryBrowserList = document.getElementById("directory-browser-list");
  const directoryBrowserUpButton = document.getElementById("directory-browser-up");
  const directoryBrowserNewButton = document.getElementById("directory-browser-new");
  const directoryBrowserSelectButton = document.getElementById("directory-browser-select");
  const directoryBrowserCreate = document.getElementById("directory-browser-create");
  const directoryBrowserCreateInput = document.getElementById("directory-browser-create-input");
  const directoryBrowserCreateConfirmButton = document.getElementById("directory-browser-create-confirm");
  const directoryBrowserCreateCancelButton = document.getElementById("directory-browser-create-cancel");
  const createModal = document.getElementById("create-modal");
  const closeCreateButton = document.getElementById("close-create");
  const cancelCreateButton = document.getElementById("cancel-create");
  const confirmCreateButton = document.getElementById("confirm-create");
  const createNameInput = document.getElementById("create-name-input");
  const createParentLabel = document.getElementById("create-parent-label");
  const createTitle = document.getElementById("create-title");
  const createHint = document.getElementById("create-hint");
  const sourceTypeSelect = document.getElementById("source-type-select");
  const localSourceSection = document.getElementById("local-source-section");
  const sftpSourceSection = document.getElementById("sftp-source-section");
  const gdriveSourceSection = document.getElementById("gdrive-source-section");
  const contentRootInput = document.getElementById("content-root-input");
  const sftpHostInput = document.getElementById("sftp-host-input");
  const sftpPortInput = document.getElementById("sftp-port-input");
  const sftpUsernameInput = document.getElementById("sftp-username-input");
  const sftpPasswordInput = document.getElementById("sftp-password-input");
  const sftpPathInput = document.getElementById("sftp-path-input");
  const gdriveFolderIdInput = document.getElementById("gdrive-folder-id-input");
  const sortModeSelect = document.getElementById("sort-mode-select");
  const themeModeSelect = document.getElementById("theme-mode-select");
  const editorFontSizeInput = document.getElementById("editor-font-size-input");
  const profileNameInput = document.getElementById("profile-name-input");
  const profileEditorTitle = document.getElementById("profile-editor-title");
  const settingsProfileList = document.getElementById("settings-profile-list");
  const imageUploadModeSelect = document.getElementById("image-upload-mode-select");
  const imageUploadSubdirInput = document.getElementById("image-upload-subdir-input");
  const imageUploadSubdirSection = document.getElementById("image-upload-subdir-section");
  const contentRootDisplay = document.getElementById("content-root-display");
  const currentFileLabel = document.getElementById("current-file-label");
  const currentFilePath = document.getElementById("current-file-path");
  const statusMessage = document.getElementById("status-message");
  const editorContainer = document.getElementById("editor");
  const previewStage = document.getElementById("preview-stage");
  const imagePreview = document.getElementById("image-preview");
  const pdfPreview = document.getElementById("pdf-preview");
  const uploadStage = document.getElementById("upload-stage");
  const uploadTargetLabel = document.getElementById("upload-target-label");
  const uploadDropzone = document.getElementById("upload-dropzone");
  const uploadSelectButton = document.getElementById("upload-select-button");
  const uploadSubmitButton = document.getElementById("upload-submit-button");
  const uploadCancelButton = document.getElementById("upload-cancel-button");
  const uploadFileInput = document.getElementById("upload-file-input");
  const uploadFileList = document.getElementById("upload-file-list");
  const treeContextMenu = document.getElementById("tree-context-menu");
  const emptyState = document.getElementById("empty-state");
  const unsupportedState = document.getElementById("unsupported-state");

  const expandedDirectories = new Set([""]);
  let treeData = null;
  let preferences = null;
  let preferenceProfiles = [];
  let editingPreferenceProfileId = null;
  let profileFormGdriveCredentials = "";
  let selectedPath = null;
  let selectedEditable = false;
  let selectedTreePath = "";
  let selectedTreeKind = "directory";
  let dragState = null;
  let createKind = "file";
  let createParentPathOverride = null;
  let modalAction = "create"; // "create" | "rename"
  let renameTargetNode = null;
  let directoryBrowserState = null;
  let directoryBrowserCreateOpen = false;
  let contextMenuState = null;
  let showHiddenFiles = false;
  let scopedRootPath = "";
  let uploadTargetPath = "";
  let pendingUploadFiles = [];
  let diagramToolbarMenu = null;
  let lastEditorSelection = null;

  function computeInsertRef(sourceMdPath, uploadedPath) {
    const sourceParts = getParentPath(sourceMdPath).split("/").filter(Boolean);
    const targetParts = uploadedPath.split("/").filter(Boolean);
    let i = 0;
    while (i < sourceParts.length && i < targetParts.length && sourceParts[i] === targetParts[i]) {
      i += 1;
    }
    const ups = sourceParts.length - i;
    const downs = targetParts.slice(i);
    return (ups > 0 ? "../".repeat(ups) : "./") + downs.join("/");
  }

  function plantUmlSvgUrl(code) {
    const hex = Array.from(new TextEncoder().encode(code))
      .map(b => b.toString(16).padStart(2, "0"))
      .join("");
    return `https://www.plantuml.com/plantuml/svg/~h${hex}`;
  }

  function insertEditorSnippet(snippet) {
    const snippetText = snippet.trimEnd();
    const originalMode = currentEditorMode;
    const selection = getStoredEditorSelection();
    let mdStart = selection[0];
    let mdEnd = selection[1];

    if (editor.isWysiwygMode()) {
      [mdStart, mdEnd] = editor.convertPosToMatchEditorMode(selection[0], selection[1], "markdown");
    }

    const current = editor.getMarkdown();
    const startOffset = markdownPositionToOffset(current, mdStart);
    const endOffset = markdownPositionToOffset(current, mdEnd);
    const next = `${current.slice(0, startOffset)}${snippetText}${current.slice(endOffset)}`;
    const caretOffset = startOffset + snippetText.length;
    const caretPos = offsetToMarkdownPosition(next, caretOffset);

    editor.setMarkdown(next, false);

    if (originalMode === "wysiwyg") {
      const [wwStart, wwEnd] = editor.convertPosToMatchEditorMode(caretPos, caretPos, "wysiwyg");
      editor.setSelection(wwStart, wwEnd);
      scheduleWysiwygDiagramRender();
    } else {
      editor.setSelection(caretPos, caretPos);
      scheduleMermaidPreviewRender();
    }

    editor.focus();
  }

  function getStoredEditorSelection() {
    if (lastEditorSelection && lastEditorSelection.mode === currentEditorMode) {
      return lastEditorSelection.selection;
    }
    return editor.getSelection();
  }

  function rememberEditorSelection() {
    lastEditorSelection = {
      mode: currentEditorMode,
      selection: editor.getSelection(),
    };
  }

  function markdownPositionToOffset(markdown, pos) {
    if (!Array.isArray(pos)) {
      return 0;
    }
    const [targetLine, targetColumn] = pos;
    const lines = markdown.split("\n");
    let offset = 0;
    for (let index = 0; index < targetLine; index += 1) {
      offset += (lines[index] || "").length + 1;
    }
    return offset + targetColumn;
  }

  function offsetToMarkdownPosition(markdown, offset) {
    const safeOffset = Math.max(0, Math.min(offset, markdown.length));
    const head = markdown.slice(0, safeOffset);
    const lines = head.split("\n");
    return [lines.length - 1, lines[lines.length - 1].length];
  }

  function buildDiagramSnippet(type) {
    switch (type) {
      case "mermaid-flowchart":
        return "```mermaid\nflowchart TD\n  A[Start] --> B[Step]\n  B --> C[Finish]\n```\n";
      case "mermaid-sequence":
        return "```mermaid\nsequenceDiagram\n  participant U as User\n  participant A as App\n  U->>A: Request\n  A-->>U: Response\n```\n";
      case "mermaid-class":
        return "```mermaid\nclassDiagram\n  class Note\n  class Folder\n  Folder --> Note\n```\n";
      case "plantuml-sequence":
        return "```plantuml\n@startuml\nAlice -> Bob: Hello\nBob --> Alice: Hi\n@enduml\n```\n";
      default:
        return "```mermaid\nflowchart TD\n  A[Start] --> B[Step]\n```\n";
    }
  }

  const editor = new toastui.Editor({
    el: editorContainer,
    height: "100%",
    initialEditType: "wysiwyg",
    previewStyle: "vertical",
    initialValue: "",
    usageStatistics: false,
    hideModeSwitch: true,
    autofocus: false,
    previewBeforeHook(markdown) {
      return decorateMarkdownForPreview(markdown, selectedPath);
    },
    customHTMLRenderer: {
      image(node) {
        const src = node.destination || "";
        if (selectedPath && !isExternalAssetTarget(src) && isEmbeddableAssetTarget(src)) {
          const assetUrl = getEmbeddedAssetUrl(selectedPath, src);
          const alt = (node.firstChild && node.firstChild.literal) || "";
          return {
            type: "openTag",
            tagName: "img",
            selfClose: true,
            attributes: { src: assetUrl, alt, class: "toastui-editor-image" },
          };
        }
        return false;
      },
      codeBlock(node) {
        // In WYSIWYG mode ProseMirror conflicts with injected divs – only intercept in preview mode.
        if (currentEditorMode !== "markdown") return false;
        const lang = (node.info || "").toLowerCase().trim();
        if (lang === "mermaid") {
          return [
            { type: "openTag", tagName: "div", classNames: ["mermaid-diagram"] },
            { type: "text", content: node.literal || "" },
            { type: "closeTag", tagName: "div" },
          ];
        }
        if (lang === "plantuml" || lang === "puml") {
          const url = plantUmlSvgUrl((node.literal || "").trim());
          return {
            type: "openTag",
            tagName: "img",
            selfClose: true,
            attributes: { src: url, class: "diagram-plantuml", alt: "PlantUML diagram" },
          };
        }
        return false;
      },
    },
  });

  // Replace ToastUI's default addImageBlobHook (which inserts a base64 data URL)
  // with our upload-to-notes-dir flow.
  function handleImageBlob(blob, insertCallback) {
    if (!selectedPath) {
      setStatus("Najpierw otworz plik Markdown.", true);
      return;
    }
    const fileDir = getParentPath(selectedPath);
    const prefs = preferences;
    let targetDir = fileDir;
    const subdir = (prefs?.image_upload_subdir || "assets").trim();
    const useSubdir = prefs?.image_upload_mode === "subdir" && subdir;
    if (useSubdir) {
      targetDir = fileDir ? `${fileDir}/${subdir}` : subdir;
    }

    const extFromType = (blob.type || "").split("/")[1] || "png";
    const fileName = blob.name && blob.name !== "image.png"
      ? blob.name
      : `image-${Date.now()}.${extFromType}`;
    const formData = new FormData();
    formData.append("parent_path", targetDir);
    formData.append("files", blob, fileName);

    const doUpload = () =>
      requestMultipart(config.uploadUrl, formData).then((result) => {
        const created = result.created_items[0];
        if (!created) {
          const skipped = result.skipped_items[0];
          setStatus(skipped?.message || "Nie udalo sie dodac obrazka.", true);
          return;
        }
        const ref = computeInsertRef(selectedPath, created.path);
        insertCallback(getEmbeddedAssetUrl(selectedPath, ref), created.name);
        setStatus(`Obraz dodany: ${created.name}`);
        loadTree();
      });

    if (useSubdir) {
      requestJson(config.createUrl, {
        method: "POST",
        body: JSON.stringify({ parent_path: fileDir, name: subdir, kind: "directory" }),
      })
        .catch(() => {})
        .then(doUpload)
        .catch((err) => setStatus(err.message, true));
    } else {
      doUpload().catch((err) => setStatus(err.message, true));
    }
  }
  editor.off("addImageBlobHook");
  editor.on("addImageBlobHook", handleImageBlob);
  editor.on("change", () => {
    rememberEditorSelection();
    scheduleMermaidPreviewRender();
    scheduleWysiwygDiagramRender();
  });
  editor.on("focus", rememberEditorSelection);
  editor.on("caretChange", rememberEditorSelection);

  function closeDiagramToolbarMenu() {
    if (!diagramToolbarMenu) return;
    diagramToolbarMenu.classList.add("hidden");
    diagramToolbarMenu.setAttribute("aria-hidden", "true");
    diagramToolbarMenu.previousElementSibling?.setAttribute("aria-expanded", "false");
  }

  function toggleDiagramToolbarMenu() {
    if (!diagramToolbarMenu) return;
    const isHidden = diagramToolbarMenu.classList.contains("hidden");
    if (!isHidden) {
      closeDiagramToolbarMenu();
      return;
    }
    diagramToolbarMenu.classList.remove("hidden");
    diagramToolbarMenu.setAttribute("aria-hidden", "false");
    diagramToolbarMenu.previousElementSibling?.setAttribute("aria-expanded", "true");
  }

  function attachDiagramToolbarButtons() {
    const toolbar = editorContainer.querySelector(".toastui-editor-defaultUI-toolbar");
    if (!toolbar || toolbar.querySelector(".noteeli-diagram-toolbar-group")) {
      return;
    }

    const group = document.createElement("div");
    group.className = "toastui-editor-toolbar-group noteeli-diagram-toolbar-group";

    const trigger = document.createElement("button");
    trigger.type = "button";
    trigger.className = "noteeli-toolbar-button noteeli-toolbar-button-dropdown";
    trigger.setAttribute("aria-label", "Wstaw diagram");
    trigger.setAttribute("aria-expanded", "false");
    trigger.title = "Wstaw diagram";
    trigger.textContent = "Diagram";
    trigger.addEventListener("mousedown", (event) => {
      event.preventDefault();
    });
    trigger.addEventListener("click", (event) => {
      event.stopPropagation();
      toggleDiagramToolbarMenu();
    });

    const menu = document.createElement("div");
    menu.className = "noteeli-toolbar-menu hidden";
    menu.setAttribute("aria-hidden", "true");

    const options = [
      { type: "mermaid-flowchart", label: "Mermaid Flowchart", message: "Dodano blok Mermaid Flowchart." },
      { type: "mermaid-sequence", label: "Mermaid Sequence", message: "Dodano blok Mermaid Sequence." },
      { type: "mermaid-class", label: "Mermaid Class", message: "Dodano blok Mermaid Class." },
      { type: "plantuml-sequence", label: "PlantUML Sequence", message: "Dodano blok PlantUML." },
    ];

    options.forEach(({ type, label, message }) => {
      const item = document.createElement("button");
      item.type = "button";
      item.className = "noteeli-toolbar-menu-item";
      item.textContent = label;
      item.addEventListener("mousedown", (event) => {
        event.preventDefault();
      });
      item.addEventListener("click", () => {
        insertEditorSnippet(buildDiagramSnippet(type));
        setStatus(message);
        scheduleWysiwygDiagramRender();
        scheduleMermaidPreviewRender();
        closeDiagramToolbarMenu();
      });
      menu.appendChild(item);
    });

    group.append(trigger, menu);
    toolbar.appendChild(group);
    diagramToolbarMenu = menu;
  }

  // ── Mermaid setup ─────────────────────────────────────────
  let currentEditorMode = "wysiwyg";

  function getMermaidTheme() {
    const t = document.body.dataset.theme;
    return t === "dark" || t === "obsidian" ? "dark" : "default";
  }

  mermaid.initialize({ startOnLoad: false, theme: getMermaidTheme(), securityLevel: "loose" });

  let mermaidPreviewTimer = null;
  let wysiwygDiagramTimer = null;

  function normalizeDiagramLanguage(value) {
    const lang = (value || "").toLowerCase().trim();
    if (lang === "plantuml" || lang === "puml") return "plantuml";
    if (lang === "mermaid") return "mermaid";
    return "";
  }

  function scheduleMermaidPreviewRender() {
    if (currentEditorMode !== "markdown") return;
    clearTimeout(mermaidPreviewTimer);
    mermaidPreviewTimer = setTimeout(() => {
      const els = editorContainer.querySelectorAll(".mermaid-diagram:not([data-processed])");
      if (els.length) mermaid.run({ nodes: Array.from(els) }).catch(() => {});
    }, 80);
  }

  function scheduleWysiwygDiagramRender() {
    if (currentEditorMode !== "wysiwyg") return;
    clearTimeout(wysiwygDiagramTimer);
    wysiwygDiagramTimer = setTimeout(() => {
      renderWysiwygDiagrams().catch(() => {});
    }, 120);
  }

  new MutationObserver(() => {
    scheduleMermaidPreviewRender();
    scheduleWysiwygDiagramRender();
  }).observe(editorContainer, { childList: true, subtree: true, characterData: true });

  async function renderWysiwygDiagrams() {
    if (currentEditorMode !== "wysiwyg") return;
    const blocks = editorContainer.querySelectorAll(".toastui-editor-ww-code-block");
    for (const block of blocks) {
      const lang = normalizeDiagramLanguage(
        block.getAttribute("data-language") ||
        block.querySelector("code")?.getAttribute("data-language") ||
        "",
      );
      const out = block.querySelector(".ww-diagram-out");
      if (!lang) {
        out?.remove();
        block.classList.remove("is-diagram-rendered", "is-source-visible");
        continue;
      }

      const code = (block.querySelector("pre code")?.textContent || block.querySelector("pre")?.textContent || "").trim();
      if (!code) {
        out?.remove();
        block.classList.remove("is-diagram-rendered", "is-source-visible");
        continue;
      }

      let nextOut = out;
      if (!nextOut) {
        nextOut = document.createElement("div");
        nextOut.className = "ww-diagram-out";
        nextOut.tabIndex = 0;
        nextOut.setAttribute("role", "button");
        nextOut.setAttribute("aria-label", "Kliknij, aby pokazac albo ukryc kod diagramu");
        nextOut.addEventListener("click", () => {
          block.classList.toggle("is-source-visible");
        });
        nextOut.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            block.classList.toggle("is-source-visible");
          }
        });
        block.appendChild(nextOut);
      }

      if (nextOut.dataset.code === code && nextOut.dataset.lang === lang) continue;
      nextOut.dataset.code = code;
      nextOut.dataset.lang = lang;

      if (lang === "mermaid") {
        nextOut.removeAttribute("data-processed");
        nextOut.textContent = code;
        const rendered = await mermaid.run({ nodes: [nextOut] }).then(() => true).catch(() => false);
        block.classList.toggle("is-diagram-rendered", rendered);
        if (!rendered) {
          block.classList.add("is-source-visible");
        }
      } else {
        nextOut.innerHTML = `<img src="${plantUmlSvgUrl(code)}" class="diagram-plantuml" alt="PlantUML diagram" />`;
        block.classList.add("is-diagram-rendered");
      }
    }
  }

  // ── Mode switch button in topbar ──────────────────────────
  editorModeToggle.addEventListener("click", () => {
    currentEditorMode = currentEditorMode === "wysiwyg" ? "markdown" : "wysiwyg";
    editor.changeMode(currentEditorMode);
    editorModeToggle.textContent = currentEditorMode === "wysiwyg" ? "WYSIWYG" : "Markdown";
    editorModeToggle.setAttribute("aria-pressed", String(currentEditorMode === "markdown"));
    if (currentEditorMode === "wysiwyg") scheduleWysiwygDiagramRender();
    else scheduleMermaidPreviewRender();
  });

  function clampFontSize(value) {
    return Math.max(12, Math.min(28, Number.parseInt(value, 10) || 16));
  }

  function applyTheme(themeMode) {
    document.body.dataset.theme = themeMode;
    shell.dataset.themeMode = themeMode;
    mermaid.initialize({ startOnLoad: false, theme: getMermaidTheme(), securityLevel: "loose" });
    if (currentEditorMode === "wysiwyg") {
      editorContainer.querySelectorAll(".ww-diagram-out").forEach((node) => {
        node.removeAttribute("data-code");
      });
      scheduleWysiwygDiagramRender();
    } else {
      editorContainer.querySelectorAll(".mermaid-diagram[data-processed]").forEach((node) => {
        node.removeAttribute("data-processed");
      });
      scheduleMermaidPreviewRender();
    }
  }

  function applyEditorFontSize(fontSize) {
    const normalized = clampFontSize(fontSize);
    document.documentElement.style.setProperty("--editor-font-size", `${normalized}px`);
    shell.dataset.editorFontSize = String(normalized);
    fontSizeLabel.textContent = `${normalized}px`;
    editorFontSizeInput.value = String(normalized);
  }

  function openSettingsModal() {
    closePreferenceProfilesDropdown();
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
    toggleDirectoryCreate(false);
  }

  function toggleDirectoryCreate(forceOpen) {
    directoryBrowserCreateOpen = typeof forceOpen === "boolean" ? forceOpen : !directoryBrowserCreateOpen;
    directoryBrowserCreate?.classList.toggle("hidden", !directoryBrowserCreateOpen);
    if (!directoryBrowserCreateOpen && directoryBrowserCreateInput) {
      directoryBrowserCreateInput.value = "";
    }
    if (directoryBrowserCreateOpen) {
      window.setTimeout(() => directoryBrowserCreateInput?.focus(), 0);
    }
  }

  function openPreferenceProfilesDropdown() {
    preferenceProfilesDropdown?.classList.remove("hidden");
    preferenceProfilesDropdown?.setAttribute("aria-hidden", "false");
    togglePreferenceProfilesButton?.setAttribute("aria-expanded", "true");
  }

  function closePreferenceProfilesDropdown() {
    preferenceProfilesDropdown?.classList.add("hidden");
    preferenceProfilesDropdown?.setAttribute("aria-hidden", "true");
    togglePreferenceProfilesButton?.setAttribute("aria-expanded", "false");
  }

  function togglePreferenceProfilesDropdown() {
    if (!preferenceProfilesDropdown || preferenceProfilesDropdown.classList.contains("hidden")) {
      openPreferenceProfilesDropdown();
      return;
    }
    closePreferenceProfilesDropdown();
  }

  function getCurrentParentPath() {
    if (!selectedTreePath) {
      return "";
    }
    return selectedTreeKind === "directory" ? selectedTreePath : getParentPath(selectedTreePath);
  }

  function openCreateModal(kind, parentPathOverride = null) {
    createKind = kind;
    createParentPathOverride = parentPathOverride;
    const parentPath = parentPathOverride ?? getCurrentParentPath();
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

  function openRenameModal(node) {
    modalAction = "rename";
    renameTargetNode = node;
    createTitle.textContent = "Zmien nazwe";
    createHint.textContent = "Podaj nowa nazwe. Rozszerzenie .md zostanie dodane automatycznie dla plikow Markdown.";
    createParentLabel.textContent = `Element: ${node.path || node.name}`;
    createNameInput.value = node.name;
    confirmCreateButton.textContent = "Zmien nazwe";
    createModal.classList.remove("hidden");
    createModal.setAttribute("aria-hidden", "false");
    window.setTimeout(() => { createNameInput.focus(); createNameInput.select(); }, 0);
  }

  function closeCreateModal() {
    createModal.classList.add("hidden");
    createModal.setAttribute("aria-hidden", "true");
    createParentPathOverride = null;
    modalAction = "create";
    renameTargetNode = null;
    confirmCreateButton.textContent = "Utworz";
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

  function applyHiddenFilesToggleState() {
    toggleHiddenFilesButton.classList.toggle("is-active", showHiddenFiles);
    toggleHiddenFilesButton.setAttribute("aria-pressed", String(showHiddenFiles));
    toggleHiddenFilesButton.setAttribute(
      "aria-label",
      showHiddenFiles ? "Ukryj ukryte pliki" : "Pokaz ukryte pliki",
    );
    toggleHiddenFilesButton.title = showHiddenFiles ? "Ukryj ukryte pliki" : "Pokaz ukryte pliki";
  }

  function applyTreeScopeState() {
    resetTreeRootButton.classList.toggle("hidden", !scopedRootPath);
    resetTreeRootButton.setAttribute("aria-hidden", String(!scopedRootPath));
  }

  function getPreviewUrl(path) {
    return `${config.previewUrl}?path=${encodeURIComponent(path)}`;
  }

  function getEmbeddedAssetUrl(sourcePath, target) {
    return `${config.embeddedAssetUrl}?source_path=${encodeURIComponent(sourcePath)}&target=${encodeURIComponent(target)}`;
  }

  function cleanEmbeddedUrls(markdown) {
    if (!markdown || !config.embeddedAssetUrl) return markdown;
    const base = config.embeddedAssetUrl.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const re = new RegExp(base + "\\?source_path=[^&)\\s]+&target=([^)\\s]+)", "g");
    return markdown.replace(re, (_, encodedTarget) => decodeURIComponent(encodedTarget));
  }

  function normalizeEmbedTarget(target) {
    let normalized = target.trim();
    if (normalized.startsWith("<") && normalized.endsWith(">")) {
      normalized = normalized.slice(1, -1);
    }
    if (normalized.includes("|")) {
      normalized = normalized.split("|", 1)[0];
    }
    if (normalized.includes("#")) {
      normalized = normalized.split("#", 1)[0];
    }
    return normalized.trim();
  }

  function isExternalAssetTarget(target) {
    return /^(https?:|data:|blob:|\/api\/)/i.test(target);
  }

  function isEmbeddableAssetTarget(target) {
    const normalized = normalizeEmbedTarget(target).toLowerCase();
    return [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp", ".avif", ".excalidraw"].some((suffix) =>
      normalized.endsWith(suffix),
    );
  }

  function toEmbeddedImageMarkdown(sourcePath, target, alt = "") {
    const normalizedTarget = normalizeEmbedTarget(target);
    if (!normalizedTarget || isExternalAssetTarget(normalizedTarget) || !isEmbeddableAssetTarget(normalizedTarget)) {
      return null;
    }
    const assetUrl = getEmbeddedAssetUrl(sourcePath, normalizedTarget);
    return `![${alt}](${assetUrl})`;
  }

  function decorateMarkdownForPreview(markdown, sourcePath) {
    if (!markdown || !sourcePath) {
      return markdown;
    }

    let transformed = markdown;
    transformed = transformed.replace(/!\[\[([^\]]+)\]\]/g, (match, target) => {
      return toEmbeddedImageMarkdown(sourcePath, target) || match;
    });
    transformed = transformed.replace(/(^|[^\!])\[\[([^\]]+)\]\]/gm, (match, prefix, target) => {
      const embedded = toEmbeddedImageMarkdown(sourcePath, target);
      return embedded ? `${prefix}${embedded}` : match;
    });
    transformed = transformed.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, (match, alt, target) => {
      return toEmbeddedImageMarkdown(sourcePath, target, alt) || match;
    });
    transformed = transformed.replace(/(^|[^\!])\[([^\]]*)\]\(([^)]+)\)/gm, (match, prefix, label, target) => {
      const embedded = toEmbeddedImageMarkdown(sourcePath, target, label);
      return embedded ? `${prefix}${embedded}` : match;
    });
    return transformed;
  }

  function hidePreview() {
    previewStage.classList.add("hidden");
    imagePreview.classList.add("hidden");
    imagePreview.removeAttribute("src");
    imagePreview.alt = "";
    pdfPreview.classList.add("hidden");
    pdfPreview.removeAttribute("src");
  }

  function hideUploadStage() {
    uploadStage.classList.add("hidden");
  }

  function showEditorMode() {
    editorContainer.classList.remove("hidden");
    hidePreview();
    hideUploadStage();
  }

  function showPreviewMode(file) {
    editorContainer.classList.add("hidden");
    previewStage.classList.remove("hidden");
    hideUploadStage();
    imagePreview.classList.toggle("hidden", file.preview_kind !== "image");
    pdfPreview.classList.toggle("hidden", file.preview_kind !== "pdf");

    const previewUrl = getPreviewUrl(file.path);
    if (file.preview_kind === "image") {
      imagePreview.src = previewUrl;
      imagePreview.alt = file.name;
      pdfPreview.removeAttribute("src");
    } else if (file.preview_kind === "pdf") {
      pdfPreview.src = previewUrl;
      imagePreview.removeAttribute("src");
      imagePreview.alt = "";
    }
  }

  function showUnsupportedMode() {
    editorContainer.classList.add("hidden");
    hidePreview();
    hideUploadStage();
  }

  function getUploadTargetLabel(path) {
    return path || "katalog glowny";
  }

  function renderUploadFileList() {
    uploadFileList.innerHTML = "";
    if (!pendingUploadFiles.length) {
      const empty = document.createElement("div");
      empty.className = "upload-file-empty muted";
      empty.textContent = "Nie wybrano jeszcze zadnych plikow.";
      uploadFileList.appendChild(empty);
      return;
    }

    const list = document.createElement("ul");
    list.className = "upload-file-items";
    pendingUploadFiles.forEach((file) => {
      const item = document.createElement("li");
      item.className = "upload-file-item";
      item.innerHTML = `
        <span class="upload-file-name">${file.name}</span>
        <span class="upload-file-size">${formatFileSize(file.size)}</span>
      `;
      list.appendChild(item);
    });
    uploadFileList.appendChild(list);
  }

  function resetUploadState() {
    pendingUploadFiles = [];
    uploadFileInput.value = "";
    renderUploadFileList();
  }

  function showUploadMode(targetPath) {
    uploadTargetPath = targetPath || "";
    editorContainer.classList.add("hidden");
    hidePreview();
    uploadStage.classList.remove("hidden");
    saveButton.disabled = true;
    selectedEditable = false;
    selectedPath = null;
    updateHeader("Upload plikow", getUploadTargetLabel(uploadTargetPath));
    uploadTargetLabel.textContent = `Docelowy katalog: ${getUploadTargetLabel(uploadTargetPath)}`;
    resetUploadState();
    toggleOverlay({ empty: false, unsupported: false });
  }

  function closeUploadMode() {
    uploadTargetPath = "";
    resetUploadState();
    showEditorMode();
    toggleOverlay({ empty: true, unsupported: false });
    updateHeader("", "");
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

  async function requestMultipart(url, formData) {
    const response = await fetch(url, {
      method: "POST",
      body: formData,
      credentials: "same-origin",
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

  function formatFileSize(size) {
    if (size < 1024) {
      return `${size} B`;
    }
    if (size < 1024 * 1024) {
      return `${(size / 1024).toFixed(1)} KB`;
    }
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
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

  function applySourceTypeVisibility(sourceType) {
    if (!localSourceSection) return;
    localSourceSection.classList.toggle("hidden", sourceType !== "local");
    sftpSourceSection?.classList.toggle("hidden", sourceType !== "sftp");
    gdriveSourceSection?.classList.toggle("hidden", sourceType !== "gdrive");
  }

  if (sourceTypeSelect) {
    sourceTypeSelect.addEventListener("change", () => applySourceTypeVisibility(sourceTypeSelect.value));
  }

  if (imageUploadModeSelect) {
    imageUploadModeSelect.addEventListener("change", () => {
      imageUploadSubdirSection?.classList.toggle("hidden", imageUploadModeSelect.value !== "subdir");
    });
  }

  function buildPreferencesPayload(overrides = {}) {
    return {
      source_type: sourceTypeSelect?.value || "local",
      content_root: contentRootInput?.value || "",
      sftp_host: sftpHostInput?.value || "",
      sftp_port: parseInt(sftpPortInput?.value || "22", 10),
      sftp_username: sftpUsernameInput?.value || "",
      sftp_password: sftpPasswordInput?.value || "",
      sftp_path: sftpPathInput?.value || "/",
      gdrive_folder_id: gdriveFolderIdInput?.value || "root",
      sort_mode: sortModeSelect.value,
      theme_mode: themeModeSelect.value,
      editor_font_size: clampFontSize(editorFontSizeInput.value),
      image_upload_mode: imageUploadModeSelect?.value || "same_dir",
      image_upload_subdir: imageUploadSubdirInput?.value?.trim() || "assets",
      ...overrides,
    };
  }

  function applyPreferencesToForm(nextPreferences) {
    if (sourceTypeSelect) sourceTypeSelect.value = nextPreferences.source_type || "local";
    if (sourceTypeSelect) sourceTypeSelect.value = nextPreferences.source_type || "local";
    if (contentRootInput) contentRootInput.value = nextPreferences.content_root;
    if (sftpHostInput) sftpHostInput.value = nextPreferences.sftp_host || "";
    if (sftpPortInput) sftpPortInput.value = nextPreferences.sftp_port || 22;
    if (sftpUsernameInput) sftpUsernameInput.value = nextPreferences.sftp_username || "";
    if (sftpPasswordInput) sftpPasswordInput.value = nextPreferences.sftp_password || "";
    if (sftpPathInput) sftpPathInput.value = nextPreferences.sftp_path || "/";
    if (gdriveFolderIdInput) gdriveFolderIdInput.value = nextPreferences.gdrive_folder_id || "root";
    sortModeSelect.value = nextPreferences.sort_mode;
    themeModeSelect.value = nextPreferences.theme_mode;
    editorFontSizeInput.value = String(nextPreferences.editor_font_size);
    if (imageUploadModeSelect) imageUploadModeSelect.value = nextPreferences.image_upload_mode || "same_dir";
    if (imageUploadSubdirInput) imageUploadSubdirInput.value = nextPreferences.image_upload_subdir || "assets";
    if (imageUploadSubdirSection) imageUploadSubdirSection.classList.toggle("hidden", nextPreferences.image_upload_mode !== "subdir");
    applySourceTypeVisibility(nextPreferences.source_type || "local");
    profileFormGdriveCredentials = nextPreferences.gdrive_credentials || "";
  }

  function applyPreferencesToUi(nextPreferences) {
    preferences = nextPreferences;
    applyPreferencesToForm(nextPreferences);
    contentRootDisplay.textContent = preferences.content_root;
    applyTheme(preferences.theme_mode);
    applyEditorFontSize(preferences.editor_font_size);
  }

  async function loadPreferences() {
    applyPreferencesToUi(await requestJson(config.preferencesUrl, { method: "GET" }));
  }

  async function persistPreferences(overrides = {}) {
    const payload = buildPreferencesPayload(overrides);
    const nextPreferences = await requestJson(config.preferencesUrl, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    applyPreferencesToUi(nextPreferences);
    return preferences;
  }

  function buildProfilePayload(overrides = {}) {
    const gdriveCredentials =
      overrides.gdrive_credentials ??
      profileFormGdriveCredentials ??
      preferences?.gdrive_credentials ??
      "";
    return {
      ...buildPreferencesPayload(overrides),
      gdrive_credentials: gdriveCredentials,
    };
  }

  function findPreferenceProfile(profileId) {
    return preferenceProfiles.find((profile) => profile.id === profileId) || null;
  }

  function resetProfileEditor({ resetForm = false } = {}) {
    editingPreferenceProfileId = null;
    if (profileEditorTitle) profileEditorTitle.textContent = "Nowy profil";
    if (saveProfileButton) saveProfileButton.textContent = "Zapamietaj";
    cancelProfileEditButton?.classList.add("hidden");
    if (profileNameInput) profileNameInput.value = "";
    if (resetForm && preferences) {
      applyPreferencesToForm(preferences);
    }
    renderSettingsPreferenceProfiles();
  }

  function startProfileEditing(profile) {
    editingPreferenceProfileId = profile.id;
    if (profileEditorTitle) profileEditorTitle.textContent = `Edytujesz: ${profile.name}`;
    if (saveProfileButton) saveProfileButton.textContent = "Zapisz zmiany";
    cancelProfileEditButton?.classList.remove("hidden");
    if (profileNameInput) profileNameInput.value = profile.name;
    applyPreferencesToForm(profile);
    renderSettingsPreferenceProfiles();
    profileNameInput?.focus();
    profileNameInput?.select();
  }

  function getProfileSummary(profile) {
    if (profile.source_type === "sftp") {
      const identity = [profile.sftp_username, profile.sftp_host].filter(Boolean).join("@");
      const remotePath = profile.sftp_path || "/";
      return identity ? `${identity}:${remotePath}` : `SFTP ${remotePath}`;
    }
    if (profile.source_type === "gdrive") {
      return `Google Drive: ${profile.gdrive_folder_id || "root"}`;
    }
    return profile.content_root;
  }

  function renderPreferenceProfiles() {
    if (!preferenceProfilesList) {
      return;
    }

    preferenceProfilesList.innerHTML = "";
    if (!preferenceProfiles.length) {
      const empty = document.createElement("div");
      empty.className = "profiles-dropdown-empty muted";
      empty.textContent = "Brak zapisanych zestawow. Utworz pierwszy profil w ustawieniach.";
      preferenceProfilesList.appendChild(empty);
      return;
    }

    preferenceProfiles.forEach((profile) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "profiles-dropdown-item";
      const title = document.createElement("strong");
      title.textContent = profile.name;
      const summary = document.createElement("span");
      summary.textContent = getProfileSummary(profile);
      button.append(title, summary);
      button.addEventListener("click", () => applyPreferenceProfile(profile.id, profile.name));
      preferenceProfilesList.appendChild(button);
    });
  }

  function renderSettingsPreferenceProfiles() {
    if (!settingsProfileList) {
      return;
    }

    settingsProfileList.innerHTML = "";
    if (!preferenceProfiles.length) {
      const empty = document.createElement("div");
      empty.className = "settings-profile-empty muted";
      empty.textContent = "Brak zapisanych profili.";
      settingsProfileList.appendChild(empty);
      return;
    }

    preferenceProfiles.forEach((profile) => {
      const row = document.createElement("div");
      row.className = "settings-profile-item";
      if (editingPreferenceProfileId === profile.id) {
        row.classList.add("is-editing");
      }

      const info = document.createElement("div");
      info.className = "settings-profile-item-info";
      const title = document.createElement("strong");
      title.textContent = profile.name;
      const summary = document.createElement("span");
      summary.textContent = getProfileSummary(profile);
      info.append(title, summary);

      const actions = document.createElement("div");
      actions.className = "settings-profile-actions";

      const editButton = document.createElement("button");
      editButton.type = "button";
      editButton.className = "button button-secondary settings-profile-action";
      editButton.textContent = "Edytuj";
      editButton.addEventListener("click", () => startProfileEditing(profile));

      const deleteButton = document.createElement("button");
      deleteButton.type = "button";
      deleteButton.className = "button button-secondary settings-profile-action";
      deleteButton.textContent = "Usun";
      deleteButton.addEventListener("click", () => deletePreferenceProfile(profile));

      actions.append(editButton, deleteButton);
      row.append(info, actions);
      settingsProfileList.appendChild(row);
    });
  }

  async function loadPreferenceProfiles() {
    const payload = await requestJson(config.preferenceProfilesUrl, { method: "GET" });
    preferenceProfiles = payload.profiles || [];
    if (editingPreferenceProfileId && !findPreferenceProfile(editingPreferenceProfileId)) {
      resetProfileEditor();
    }
    renderPreferenceProfiles();
    renderSettingsPreferenceProfiles();
  }

  async function saveCurrentPreferenceProfile() {
    const profileName = profileNameInput?.value.trim() || "";
    if (!profileName) {
      setStatus("Podaj nazwe profilu.", true);
      profileNameInput?.focus();
      return;
    }

    try {
      const isEditing = editingPreferenceProfileId !== null;
      setStatus(isEditing ? "Aktualizuje profil ustawien..." : "Zapisuje profil ustawien...");
      const url = isEditing ? `${config.preferenceProfilesUrl}/${editingPreferenceProfileId}` : config.preferenceProfilesUrl;
      const method = isEditing ? "PUT" : "POST";
      const profile = await requestJson(url, {
        method,
        body: JSON.stringify(buildProfilePayload({ name: profileName })),
      });
      await loadPreferenceProfiles();
      resetProfileEditor();
      setStatus(isEditing ? `Profil zaktualizowany: ${profile.name}.` : `Profil zapisany: ${profile.name}.`);
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  async function deletePreferenceProfile(profile) {
    if (!window.confirm(`Usunac profil "${profile.name}"?`)) {
      return;
    }

    try {
      setStatus(`Usuwam profil: ${profile.name}...`);
      await requestJson(`${config.preferenceProfilesUrl}/${profile.id}`, {
        method: "DELETE",
      });
      if (editingPreferenceProfileId === profile.id) {
        resetProfileEditor({ resetForm: true });
      }
      await loadPreferenceProfiles();
      setStatus(`Profil usuniety: ${profile.name}.`);
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  async function resetWorkspaceAfterPreferencesChange() {
    selectedPath = null;
    selectedEditable = false;
    saveButton.disabled = true;
    updateHeader("", "");
    showEditorMode();
    editor.setMarkdown("", false);
    toggleOverlay({ empty: true, unsupported: false });
    await loadTree({ autoSelect: true });
  }

  async function applyPreferenceProfile(profileId, profileName = "") {
    try {
      setStatus(`Laduje profil${profileName ? `: ${profileName}` : ""}...`);
      const nextPreferences = await requestJson(`${config.preferenceProfilesUrl}/${profileId}/apply`, {
        method: "POST",
      });
      applyPreferencesToUi(nextPreferences);
      closePreferenceProfilesDropdown();
      await resetWorkspaceAfterPreferencesChange();
      setStatus(profileName ? `Zaladowano profil: ${profileName}.` : "Profil zaladowany.");
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  function getParentPath(path) {
    const parts = path.split("/");
    return parts.length > 1 ? parts.slice(0, -1).join("/") : "";
  }

  function getParentPathForNode(node) {
    return node.kind === "directory" ? node.path : getParentPath(node.path);
  }

  function closeTreeContextMenu() {
    treeContextMenu.classList.add("hidden");
    treeContextMenu.setAttribute("aria-hidden", "true");
    treeContextMenu.innerHTML = "";
    contextMenuState = null;
  }

  function positionTreeContextMenu(x, y) {
    treeContextMenu.style.left = `${x}px`;
    treeContextMenu.style.top = `${y}px`;

    requestAnimationFrame(() => {
      const rect = treeContextMenu.getBoundingClientRect();
      const nextLeft = Math.min(x, window.innerWidth - rect.width - 12);
      const nextTop = Math.min(y, window.innerHeight - rect.height - 12);
      treeContextMenu.style.left = `${Math.max(12, nextLeft)}px`;
      treeContextMenu.style.top = `${Math.max(12, nextTop)}px`;
    });
  }

  async function deleteItem(node) {
    try {
      const resp = await fetch(`${config.deleteUrl}?path=${encodeURIComponent(node.path)}`, { method: "DELETE" });
      if (!resp.ok) {
        const data = await resp.json().catch(() => ({}));
        setStatus(data.detail || "Blad usuwania.", true);
        return;
      }
      if (selectedTreePath === node.path) {
        selectedTreePath = "";
        selectedTreeKind = "directory";
        toggleOverlay({ empty: true });
      }
      await loadTree();
      setStatus(`Usunieto: ${node.name}.`);
    } catch {
      setStatus("Blad polaczenia przy usuwaniu.", true);
    }
  }

  function createContextMenuButton(label, onClick, tone = "default", skipClose = false) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `context-menu-item context-menu-item-${tone}`;
    button.textContent = label;
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      if (!skipClose) closeTreeContextMenu();
      await onClick();
    });
    return button;
  }

  function renderTreeContextMenu() {
    if (!contextMenuState) {
      return;
    }

    const { node } = contextMenuState;
    const parentPath = getParentPathForNode(node);
    const uploadPath = node.kind === "directory" ? node.path : parentPath;
    treeContextMenu.innerHTML = "";

    const header = document.createElement("div");
    header.className = "context-menu-header";
    header.innerHTML = `
      <strong class="context-menu-title">${node.name}</strong>
      <span class="context-menu-path">${node.path || "/"}</span>
    `;
    treeContextMenu.appendChild(header);

    if (node.kind === "directory") {
      treeContextMenu.appendChild(
        createContextMenuButton(expandedDirectories.has(node.path) ? "Zwin katalog" : "Rozwin katalog", async () => {
          selectedTreePath = node.path;
          selectedTreeKind = "directory";
          if (expandedDirectories.has(node.path)) {
            expandedDirectories.delete(node.path);
          } else {
            expandedDirectories.add(node.path);
          }
          renderTree(treeData);
        }),
      );
      treeContextMenu.appendChild(
        createContextMenuButton("Ustaw jako root tymczasowy", async () => {
          setScopedRoot(node.path);
          setStatus(`Pokazuje tylko ${node.path}.`);
        }),
      );
    } else {
      treeContextMenu.appendChild(
        createContextMenuButton("Otworz", async () => {
          await loadFile(node.path);
        }),
      );
    }

    treeContextMenu.appendChild(
      createContextMenuButton("Upload tutaj", async () => {
        showUploadMode(uploadPath);
        setStatus(`Przygotowano upload do ${getUploadTargetLabel(uploadPath)}.`);
      }),
    );
    treeContextMenu.appendChild(
      createContextMenuButton("Nowy plik tutaj", async () => {
        openCreateModal("file", parentPath);
      }),
    );
    treeContextMenu.appendChild(
      createContextMenuButton("Nowy katalog tutaj", async () => {
        openCreateModal("directory", parentPath);
      }),
    );
    treeContextMenu.appendChild(
      createContextMenuButton(node.kind === "directory" ? "Pobierz jako ZIP" : "Pobierz", async () => {
        window.location.href = `${config.downloadUrl}?path=${encodeURIComponent(node.path)}`;
        setStatus(node.kind === "directory" ? "Przygotowuje archiwum ZIP..." : "Rozpoczynam pobieranie pliku.");
      }),
    );
    treeContextMenu.appendChild(
      createContextMenuButton("Kopiuj sciezke", async () => {
        try {
          await navigator.clipboard.writeText(node.path);
          setStatus("Sciezka skopiowana.");
        } catch (error) {
          setStatus("Nie udalo sie skopiowac sciezki.", true);
        }
      }),
    );
    treeContextMenu.appendChild(
      createContextMenuButton("Zmien nazwe", async () => {
        openRenameModal(node);
      }),
    );
    treeContextMenu.appendChild(
      createContextMenuButton("Odswiez drzewo", async () => {
        await loadTree();
      }, "muted"),
    );

    const isConfirming = contextMenuState.deleteConfirm === true;
    treeContextMenu.appendChild(
      createContextMenuButton(
        isConfirming ? "Kliknij ponownie aby potwierdzic" : "Usun",
        async () => {
          if (isConfirming) {
            contextMenuState.deleteConfirm = false;
            await deleteItem(node);
          } else {
            contextMenuState.deleteConfirm = true;
            renderTreeContextMenu();
          }
        },
        isConfirming ? "danger" : "muted",
        true,
      ),
    );
  }

  function openTreeContextMenu(event, node) {
    event.preventDefault();
    contextMenuState = { node };
    renderTreeContextMenu();
    treeContextMenu.classList.remove("hidden");
    treeContextMenu.setAttribute("aria-hidden", "false");
    positionTreeContextMenu(event.clientX, event.clientY);
  }

  function renderDirectoryBrowser(payload) {
    directoryBrowserState = payload;
    renderDirectoryBrowserPath(payload.current_path);
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
      const name = document.createElement("span");
      name.className = "directory-browser-item-name";
      name.textContent = directory.name;
      const path = document.createElement("span");
      path.className = "directory-browser-item-path";
      path.textContent = directory.path;
      const arrow = document.createElement("span");
      arrow.className = "directory-browser-item-arrow";
      arrow.textContent = "›";
      button.append(name, path, arrow);
      button.addEventListener("click", () => {
        loadDirectoryBrowser(directory.path);
      });
      directoryBrowserList.appendChild(button);
    });
  }

  function renderDirectoryBrowserPath(path) {
    if (!directoryBrowserCurrentPath) {
      return;
    }

    directoryBrowserCurrentPath.innerHTML = "";
    const normalized = path || "/";
    if (normalized === "/") {
      const rootButton = document.createElement("button");
      rootButton.type = "button";
      rootButton.className = "directory-browser-crumb is-current";
      rootButton.textContent = "/";
      rootButton.disabled = true;
      directoryBrowserCurrentPath.appendChild(rootButton);
      return;
    }

    const segments = normalized.split("/").filter(Boolean);
    let currentPath = normalized.startsWith("/") ? "/" : "";
    const rootButton = document.createElement("button");
    rootButton.type = "button";
    rootButton.className = "directory-browser-crumb";
    rootButton.textContent = normalized.startsWith("/") ? "/" : segments[0];
    rootButton.addEventListener("click", () => loadDirectoryBrowser(normalized.startsWith("/") ? "/" : segments[0]));
    directoryBrowserCurrentPath.appendChild(rootButton);

    if (!normalized.startsWith("/") && segments.length) {
      currentPath = segments[0];
      segments.shift();
    }

    segments.forEach((segment, index) => {
      const separator = document.createElement("span");
      separator.className = "directory-browser-separator";
      separator.textContent = "›";
      directoryBrowserCurrentPath.appendChild(separator);

      currentPath = currentPath === "/" ? `/${segment}` : `${currentPath}/${segment}`;
      const targetPath = currentPath;
      const crumb = document.createElement("button");
      crumb.type = "button";
      crumb.className = "directory-browser-crumb";
      crumb.textContent = segment;
      const isLast = index === segments.length - 1;
      if (isLast) {
        crumb.classList.add("is-current");
        crumb.disabled = true;
      } else {
        crumb.addEventListener("click", () => loadDirectoryBrowser(targetPath));
      }
      directoryBrowserCurrentPath.appendChild(crumb);
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
      toggleDirectoryCreate(false);
      setStatus("Mozesz wybrac katalog.");
    } catch (error) {
      closeDirectoryBrowserModal();
      setStatus(error.message, true);
    }
  }

  async function createDirectoryFromBrowser() {
    const name = directoryBrowserCreateInput?.value.trim() || "";
    if (!directoryBrowserState?.current_path) {
      return;
    }
    if (!name) {
      setStatus("Podaj nazwe nowego folderu.", true);
      directoryBrowserCreateInput?.focus();
      return;
    }

    try {
      setStatus("Tworze nowy folder...");
      const payload = await requestJson(config.createDirectoryUrl, {
        method: "POST",
        body: JSON.stringify({
          parent_path: directoryBrowserState.current_path,
          name,
        }),
      });
      renderDirectoryBrowser(payload);
      toggleDirectoryCreate(false);
      setStatus(`Utworzono folder: ${name}.`);
    } catch (error) {
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

  function getScopedRootNode(node) {
    if (!scopedRootPath) {
      return node;
    }
    return findDirectoryNode(node, scopedRootPath) || node;
  }

  function setScopedRoot(path) {
    scopedRootPath = path || "";
    applyTreeScopeState();
    renderTree(treeData);
  }

  function isHiddenNode(node) {
    return node.name.startsWith(".");
  }

  function filterVisibleTree(node) {
    if (showHiddenFiles || !node.children?.length) {
      return node;
    }

    return {
      ...node,
      children: node.children
        .filter((child) => !isHiddenNode(child))
        .map((child) => (child.kind === "directory" ? filterVisibleTree(child) : child)),
    };
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

  function makeSvgIcon(d) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("aria-hidden", "true");
    svg.style.cssText = "fill:currentColor;flex-shrink:0;display:block";
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", d);
    svg.appendChild(path);
    return svg;
  }

  const TREE_ICONS = {
    chevronRight: "M10 6 8.59 7.41 13.17 12l-4.58 4.59L10 18l6-6z",
    chevronDown: "M16.59 8.59 12 13.17 7.41 8.59 6 10l6 6 6-6z",
    folderClosed: "M10 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2h-8l-2-2z",
    folderOpen: "M20 6h-8l-2-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2zm0 12H4V8h16v10z",
    fileMd: "M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm4 18H6V4h7v5h5v11zm-5-5H9v-2h4v2zm2-4H9v-2h6v2z",
    fileImage: "M21 19V5c0-1.1-.9-2-2-2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2zM8.5 13.5l2.5 3.01L14.5 12l4.5 6H5l3.5-4.5z",
    filePdf: "M20 2H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8.5 7.5c0 .83-.67 1.5-1.5 1.5H9v2H7.5V7H10c.83 0 1.5.67 1.5 1.5v1zm5 2c0 .83-.67 1.5-1.5 1.5h-2.5V7H15c.83 0 1.5.67 1.5 1.5v3zm4-3H19v1h1.5V11H19v2h-1.5V7h3v1.5zM9 9.5h1v-1H9v1zM4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm10 5.5h1v-3h-1v3z",
    fileGeneric: "M14 2H6c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V8l-6-6zm4 18H6V4h7v5h5v11z",
  };

  function getFileIconInfo(name) {
    const ext = (name.split(".").pop() || "").toLowerCase();
    if (["jpg", "jpeg", "png", "gif", "webp", "svg", "bmp", "ico", "avif"].includes(ext))
      return { d: TREE_ICONS.fileImage, cls: "tree-icon-image" };
    if (ext === "pdf")
      return { d: TREE_ICONS.filePdf, cls: "tree-icon-pdf" };
    if (ext === "md" || ext === "markdown")
      return { d: TREE_ICONS.fileMd, cls: "tree-icon-md" };
    return { d: TREE_ICONS.fileGeneric, cls: "tree-icon-generic" };
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
      toggle.appendChild(makeSvgIcon(isExpanded ? TREE_ICONS.chevronDown : TREE_ICONS.chevronRight));
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
      label.className = "tree-link tree-link-dir";
      const folderIconSpan = document.createElement("span");
      folderIconSpan.className = "tree-icon tree-icon-folder";
      folderIconSpan.appendChild(makeSvgIcon(isExpanded ? TREE_ICONS.folderOpen : TREE_ICONS.folderClosed));
      label.appendChild(folderIconSpan);
      label.appendChild(document.createTextNode(node.name));
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
      row.addEventListener("contextmenu", (event) => openTreeContextMenu(event, node));
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
    spacer.className = "tree-toggle tree-toggle-file";
    const fileIconInfo = getFileIconInfo(node.name);
    const fileIconSpan = document.createElement("span");
    fileIconSpan.className = `tree-icon ${fileIconInfo.cls}`;
    fileIconSpan.appendChild(makeSvgIcon(fileIconInfo.d));
    spacer.appendChild(fileIconSpan);
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
    row.addEventListener("contextmenu", (event) => openTreeContextMenu(event, node));
    enableDragAndDrop(row, node);
    listItem.appendChild(row);

    return listItem;
  }

  function renderTree(node) {
    treeRoot.innerHTML = "";
    if (!node) {
      return;
    }

    const scopedNode = getScopedRootNode(node);
    const visibleNode = filterVisibleTree(scopedNode);

    if (scopedRootPath && visibleNode.path) {
      const scopeBar = document.createElement("div");
      scopeBar.className = "tree-scope-bar";

      const upButton = document.createElement("button");
      upButton.type = "button";
      upButton.className = "tree-scope-up";
      upButton.textContent = "..";
      upButton.title = "Poziom wyzej";
      upButton.addEventListener("click", () => {
        const parentPath = getParentPath(visibleNode.path);
        setScopedRoot(parentPath);
        setStatus(parentPath ? "Pokazuje katalog nadrzedny." : "Wrocono do pelnego drzewa.");
      });
      scopeBar.appendChild(upButton);

      const label = document.createElement("div");
      label.className = "tree-scope-label";
      label.textContent = visibleNode.path;
      scopeBar.appendChild(label);

      treeRoot.appendChild(scopeBar);
    }

    const list = document.createElement("ul");
    list.className = "tree-list tree-list-root";
    visibleNode.children.forEach((child) => list.appendChild(renderNode(child)));
    treeRoot.appendChild(list);
  }

  async function loadTree({ autoSelect = false } = {}) {
    closeTreeContextMenu();
    setStatus("Odswiezam drzewo plikow...");
    treeData = await requestJson(config.treeUrl, { method: "GET" });
    if (scopedRootPath && !findDirectoryNode(treeData, scopedRootPath)) {
      scopedRootPath = "";
      applyTreeScopeState();
    }
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
        showEditorMode();
        editor.setMarkdown(file.content || "", false);
        setTimeout(renderWysiwygDiagrams, 200);
        toggleOverlay({ empty: false, unsupported: false });
        setStatus("Plik gotowy do edycji.");
      } else if (file.previewable) {
        showPreviewMode(file);
        editor.setMarkdown("", false);
        toggleOverlay({ empty: false, unsupported: false });
        setStatus(file.preview_kind === "pdf" ? "Podglad PDF gotowy." : "Podglad obrazu gotowy.");
      } else {
        showUnsupportedMode();
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
          content: cleanEmbeddedUrls(editor.getMarkdown()),
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
      closeSettingsModal();
      await resetWorkspaceAfterPreferencesChange();
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
    const parentPath = createParentPathOverride ?? getCurrentParentPath();
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

  async function renameItem() {
    const node = renameTargetNode;
    const newName = createNameInput.value.trim();
    if (!newName) {
      setStatus("Podaj nowa nazwe.", true);
      createNameInput.focus();
      return;
    }
    try {
      setStatus("Zmieniam nazwe...");
      const renamed = await requestJson(config.renameUrl, {
        method: "POST",
        body: JSON.stringify({ path: node.path, new_name: newName }),
      });
      if (selectedTreePath === node.path) {
        selectedTreePath = renamed.path;
        selectedTreeKind = renamed.kind;
        if (renamed.kind === "file") await loadFile(renamed.path);
      }
      closeCreateModal();
      await loadTree();
      setStatus(`Zmieniono nazwe na: ${renamed.name}.`);
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  function addPendingUploadFiles(fileList) {
    const nextFiles = Array.from(fileList || []);
    if (!nextFiles.length) {
      return;
    }

    const knownKeys = new Set(pendingUploadFiles.map((file) => `${file.name}:${file.size}:${file.lastModified}`));
    nextFiles.forEach((file) => {
      const key = `${file.name}:${file.size}:${file.lastModified}`;
      if (!knownKeys.has(key)) {
        pendingUploadFiles.push(file);
        knownKeys.add(key);
      }
    });
    renderUploadFileList();
  }

  async function submitUpload() {
    if (!pendingUploadFiles.length) {
      setStatus("Najpierw wybierz pliki do uploadu.", true);
      return;
    }

    try {
      setStatus("Wysylam pliki...");
      const formData = new FormData();
      formData.append("parent_path", uploadTargetPath);
      pendingUploadFiles.forEach((file) => {
        formData.append("files", file);
      });

      const result = await requestMultipart(config.uploadUrl, formData);
      if (uploadTargetPath) {
        expandedDirectories.add(uploadTargetPath);
      }
      await loadTree();
      renderTree(treeData);

      const createdCount = result.created_items.length;
      const skippedCount = result.skipped_items.length;
      resetUploadState();

      if (skippedCount) {
        const firstMessage = result.skipped_items[0]?.message || "Czesc plikow nie zostala dodana.";
        setStatus(`Dodano ${createdCount} plikow, pominieto ${skippedCount}. ${firstMessage}`, true);
      } else {
        setStatus(`Dodano ${createdCount} plikow.`);
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
  resetTreeRootButton.addEventListener("click", () => {
    setScopedRoot("");
    setStatus("Wrocono do pelnego drzewa.");
  });
  toggleHiddenFilesButton.addEventListener("click", () => {
    showHiddenFiles = !showHiddenFiles;
    applyHiddenFilesToggleState();
    renderTree(treeData);
    setStatus(showHiddenFiles ? "Ukryte pliki sa widoczne." : "Ukryte pliki sa ukryte.");
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
  uploadSelectButton.addEventListener("click", () => uploadFileInput.click());
  uploadSubmitButton.addEventListener("click", submitUpload);
  uploadCancelButton.addEventListener("click", closeUploadMode);
  uploadFileInput.addEventListener("change", (event) => {
    addPendingUploadFiles(event.target.files);
    uploadFileInput.value = "";
  });
  uploadDropzone.addEventListener("click", (event) => {
    if (event.target.closest("button")) {
      return;
    }
    uploadFileInput.click();
  });
  uploadDropzone.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      uploadFileInput.click();
    }
  });
  uploadDropzone.addEventListener("dragover", (event) => {
    event.preventDefault();
    uploadDropzone.classList.add("is-dragover");
  });
  uploadDropzone.addEventListener("dragleave", (event) => {
    if (!uploadDropzone.contains(event.relatedTarget)) {
      uploadDropzone.classList.remove("is-dragover");
    }
  });
  uploadDropzone.addEventListener("drop", (event) => {
    event.preventDefault();
    uploadDropzone.classList.remove("is-dragover");
    addPendingUploadFiles(event.dataTransfer.files);
  });
  togglePreferenceProfilesButton?.addEventListener("click", togglePreferenceProfilesDropdown);
  openSettingsButton.addEventListener("click", openSettingsModal);
  closeSettingsButton.addEventListener("click", closeSettingsModal);
  cancelSettingsButton.addEventListener("click", closeSettingsModal);
  saveProfileButton?.addEventListener("click", saveCurrentPreferenceProfile);
  cancelProfileEditButton?.addEventListener("click", () => resetProfileEditor({ resetForm: true }));
  browseContentRootButton.addEventListener("click", openDirectoryBrowser);
  closeDirectoryBrowserButton.addEventListener("click", closeDirectoryBrowserModal);
  cancelDirectoryBrowserButton.addEventListener("click", closeDirectoryBrowserModal);
  directoryBrowserNewButton?.addEventListener("click", () => toggleDirectoryCreate());
  directoryBrowserCreateConfirmButton?.addEventListener("click", createDirectoryFromBrowser);
  directoryBrowserCreateCancelButton?.addEventListener("click", () => toggleDirectoryCreate(false));
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
  document.addEventListener("click", (event) => {
    if (!treeContextMenu.classList.contains("hidden") && !treeContextMenu.contains(event.target)) {
      closeTreeContextMenu();
    }
    if (
      diagramToolbarMenu &&
      !diagramToolbarMenu.classList.contains("hidden") &&
      !diagramToolbarMenu.parentElement?.contains(event.target)
    ) {
      closeDiagramToolbarMenu();
    }
    if (
      preferenceProfilesDropdown &&
      !preferenceProfilesDropdown.classList.contains("hidden") &&
      !preferenceProfilesDropdown.contains(event.target) &&
      !togglePreferenceProfilesButton?.contains(event.target)
    ) {
      closePreferenceProfilesDropdown();
    }
  });
  document.addEventListener("contextmenu", (event) => {
    if (!event.target.closest(".tree-row")) {
      closeTreeContextMenu();
    }
  });
  window.addEventListener("resize", closeTreeContextMenu);
  treeRoot.addEventListener("scroll", closeTreeContextMenu);
  directoryBrowserModal.addEventListener("click", (event) => {
    if (event.target === directoryBrowserModal) {
      closeDirectoryBrowserModal();
    }
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !treeContextMenu.classList.contains("hidden")) {
      closeTreeContextMenu();
      return;
    }
    if (event.key === "Escape" && diagramToolbarMenu && !diagramToolbarMenu.classList.contains("hidden")) {
      closeDiagramToolbarMenu();
      return;
    }
    if (event.key === "Escape" && preferenceProfilesDropdown && !preferenceProfilesDropdown.classList.contains("hidden")) {
      closePreferenceProfilesDropdown();
      return;
    }
    if (event.key === "Escape" && !directoryBrowserModal.classList.contains("hidden")) {
      if (directoryBrowserCreateOpen) {
        toggleDirectoryCreate(false);
        return;
      }
      closeDirectoryBrowserModal();
      return;
    }
    if (event.key === "Escape" && !settingsModal.classList.contains("hidden")) {
      closeSettingsModal();
    }
    if (event.key === "Escape" && !createModal.classList.contains("hidden")) {
      closeCreateModal();
    }
    if (event.key === "Escape" && !uploadStage.classList.contains("hidden")) {
      closeUploadMode();
    }
    if (event.key === "Enter" && document.activeElement === createNameInput && !createModal.classList.contains("hidden")) {
      createItem();
    }
    if (event.key === "Enter" && document.activeElement === directoryBrowserCreateInput && directoryBrowserCreateOpen) {
      createDirectoryFromBrowser();
    }
  });
  closeCreateButton.addEventListener("click", closeCreateModal);
  cancelCreateButton.addEventListener("click", closeCreateModal);
  confirmCreateButton.addEventListener("click", () => {
    if (modalAction === "rename") renameItem();
    else createItem();
  });
  createModal.addEventListener("click", (event) => {
    if (event.target === createModal) {
      closeCreateModal();
    }
  });
  saveButton.addEventListener("click", saveFile);
  saveSettingsButton.addEventListener("click", saveSettings);

  applyTheme(shell.dataset.themeMode || "light");
  applyEditorFontSize(shell.dataset.editorFontSize || "16");
  applyHiddenFilesToggleState();
  applyTreeScopeState();
  renderUploadFileList();
  showEditorMode();
  attachDiagramToolbarButtons();
  toggleOverlay({ empty: true, unsupported: false });
  loadPreferences()
    .then(() => loadPreferenceProfiles())
    .then(() => loadTree({ autoSelect: true }))
    .catch((error) => setStatus(error.message, true));
}
