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
  const languageSelect = document.getElementById("language-select");
  const editorFontSizeInput = document.getElementById("editor-font-size-input");
  const autosaveEnabledInput = document.getElementById("autosave-enabled-input");
  const profileNameInput = document.getElementById("profile-name-input");
  const profileEditorTitle = document.getElementById("profile-editor-title");
  const settingsProfileList = document.getElementById("settings-profile-list");
  const imageUploadModeSelect = document.getElementById("image-upload-mode-select");
  const imageUploadSubdirInput = document.getElementById("image-upload-subdir-input");
  const imageUploadSubdirSection = document.getElementById("image-upload-subdir-section");
  const sidebarEl = document.getElementById("sidebar");
  const sidebarToggleBtn = document.getElementById("sidebar-toggle");
  const sidebarPinBtn = document.getElementById("sidebar-pin");
  const sidebarResizeHandle = document.getElementById("sidebar-resize-handle");
  const contentRootDisplay = document.getElementById("content-root-display");
  const currentFileLabel = document.getElementById("current-file-label");
  const currentFilePath = document.getElementById("current-file-path");
  const statusMessage = document.getElementById("status-message");
  const editorContainer = document.getElementById("editor");
  const jsonEditorContainer = document.getElementById("json-editor");
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
  let selectedFileType = "markdown"; // "markdown" | "json"
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
  let diagramToolbarTrigger = null;
  let lastEditorSelection = null;
  let editorDirty = false;
  let isApplyingDocument = false;
  let autosaveTimer = null;
  let autosaveInFlight = false;
  let autosaveQueued = false;

  const AUTOSAVE_DELAY_MS = 1200;

  // ---------------------------------------------------------------------------
  // Sidebar — collapse / overlay / resize
  // ---------------------------------------------------------------------------

  const SIDEBAR_DEFAULT_WIDTH = 300;
  const SIDEBAR_MIN_WIDTH = 200;
  const SIDEBAR_MAX_WIDTH = 520;
  const MOBILE_BREAKPOINT = 768;

  // Persisted state
  let sidebarWidth = parseInt(localStorage.getItem("sidebar-width") || SIDEBAR_DEFAULT_WIDTH, 10);
  // "docked" | "collapsed" | "overlay"
  let sidebarMode = localStorage.getItem("sidebar-mode") || "docked";

  function isMobile() {
    return window.innerWidth <= MOBILE_BREAKPOINT;
  }

  function applyBodySidebarMode(mode) {
    shell.classList.remove("sidebar-docked", "sidebar-collapsed", "sidebar-overlay");
    shell.classList.add(`sidebar-${mode}`);

    // --sidebar-open-w is always the actual panel width for overlay/mobile display
    shell.style.setProperty("--sidebar-open-w", sidebarWidth + "px");

    // --sidebar-w controls the CSS grid column (instant change — no @property transition).
    if (mode === "docked") {
      shell.style.setProperty("--sidebar-w", sidebarWidth + "px");
    } else {
      shell.style.setProperty("--sidebar-w", "0px");
    }

    // Belt-and-suspenders: also set opacity/pointer-events via inline style
    // so collapsed state works even if CSS class specificity is ever beaten.
    if (sidebarEl) {
      if (mode === "collapsed") {
        sidebarEl.style.opacity = "0";
        sidebarEl.style.pointerEvents = "none";
      } else {
        sidebarEl.style.opacity = "";
        sidebarEl.style.pointerEvents = "";
      }
    }

    const isOpen = mode === "docked" || mode === "overlay";
    if (sidebarToggleBtn) {
      sidebarToggleBtn.setAttribute("aria-expanded", String(isOpen));
      sidebarToggleBtn.title = isOpen ? "Collapse sidebar" : "Open sidebar";
    }
  }

  function setSidebarWidth(w) {
    sidebarWidth = Math.max(SIDEBAR_MIN_WIDTH, Math.min(SIDEBAR_MAX_WIDTH, w));
    localStorage.setItem("sidebar-width", sidebarWidth);
    // Update both variables; grid column only if docked
    shell.style.setProperty("--sidebar-open-w", sidebarWidth + "px");
    if (sidebarMode === "docked") {
      shell.style.setProperty("--sidebar-w", sidebarWidth + "px");
    }
  }

  function setSidebarMode(mode) {
    sidebarMode = mode;
    applyBodySidebarMode(mode);
    if (mode !== "overlay") {
      localStorage.setItem("sidebar-mode", mode);
    }
  }

  function toggleSidebar() {
    if (isMobile()) {
      // Mobile: toggle between overlay and collapsed only
      setSidebarMode(sidebarMode === "overlay" ? "collapsed" : "overlay");
      return;
    }
    if (sidebarMode === "docked") {
      setSidebarMode("collapsed");
    } else if (sidebarMode === "collapsed") {
      setSidebarMode("overlay");
    } else {
      // overlay → collapsed
      setSidebarMode("collapsed");
    }
  }

  function pinSidebar() {
    // Dock the sidebar (pin it into the layout) and persist
    setSidebarMode("docked");
    localStorage.setItem("sidebar-mode", "docked");
  }

  function closeSidebarOverlay() {
    if (sidebarMode === "overlay") setSidebarMode("collapsed");
  }

  function initSidebar() {
    // On mobile, never start docked.
    // On medium-width viewports, also collapse if sidebar is wider than available space.
    if (sidebarMode === "docked" && (isMobile() || window.innerWidth - sidebarWidth < 420)) {
      sidebarMode = "collapsed";
    }

    // applyBodySidebarMode sets --sidebar-w, --sidebar-open-w, classes, and aria
    applyBodySidebarMode(sidebarMode);

    // Hamburger toggle
    if (sidebarToggleBtn) {
      sidebarToggleBtn.addEventListener("click", toggleSidebar);
    }

    // Pin button
    if (sidebarPinBtn) {
      sidebarPinBtn.addEventListener("click", pinSidebar);
    }

    // Click on backdrop closes overlay
    shell.addEventListener("click", (e) => {
      if (sidebarMode !== "overlay") return;
      if (
        sidebarEl &&
        !sidebarEl.contains(e.target) &&
        !(sidebarToggleBtn && sidebarToggleBtn.contains(e.target))
      ) {
        closeSidebarOverlay();
      }
    });

    // Drag to resize
    if (sidebarResizeHandle) {
      let startX = 0;
      let startW = 0;

      const onMove = (e) => {
        const dx = (e.touches ? e.touches[0].clientX : e.clientX) - startX;
        setSidebarWidth(startW + dx);
      };

      const onUp = () => {
        sidebarResizeHandle.classList.remove("is-dragging");
        document.removeEventListener("mousemove", onMove);
        document.removeEventListener("mouseup", onUp);
        document.removeEventListener("touchmove", onMove);
        document.removeEventListener("touchend", onUp);
        document.body.style.cursor = "";
        document.body.style.userSelect = "";
        // Re-enable CSS transitions after drag
        shell.style.transition = "";
      };

      sidebarResizeHandle.addEventListener("mousedown", (e) => {
        e.preventDefault();
        startX = e.clientX;
        startW = sidebarWidth;
        sidebarResizeHandle.classList.add("is-dragging");
        document.body.style.cursor = "col-resize";
        document.body.style.userSelect = "none";
        // Disable CSS transitions during drag for instant feedback
        shell.style.transition = "none";
        document.addEventListener("mousemove", onMove);
        document.addEventListener("mouseup", onUp);
      });
    }

    // Auto-collapse on resize:
    //   • always on mobile (≤768 px)
    //   • on wider viewports when sidebar would leave < 420 px for the workspace
    window.addEventListener("resize", () => {
      if (sidebarMode !== "docked") return;
      if (isMobile() || window.innerWidth - sidebarWidth < 420) {
        setSidebarMode("collapsed");
      }
    });
  }

  initSidebar();

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
      try {
        [mdStart, mdEnd] = editor.convertPosToMatchEditorMode(selection[0], selection[1], "markdown");
      } catch (_) {
        mdStart = null;
        mdEnd = null;
      }
    }

    const current = editor.getMarkdown();
    const startOffset = mdStart != null ? markdownPositionToOffset(current, mdStart) : current.length;
    const endOffset = mdEnd != null ? markdownPositionToOffset(current, mdEnd) : current.length;
    const sep = startOffset > 0 && current[startOffset - 1] !== "\n" ? "\n" : "";
    const next = `${current.slice(0, startOffset)}${sep}${snippetText}\n${current.slice(endOffset)}`;
    const caretOffset = startOffset + sep.length + snippetText.length + 1;
    const caretPos = offsetToMarkdownPosition(next, caretOffset);

    editor.setMarkdown(next, false);

    if (originalMode === "wysiwyg") {
      try {
        const [wwStart, wwEnd] = editor.convertPosToMatchEditorMode(caretPos, caretPos, "wysiwyg");
        editor.setSelection(wwStart, wwEnd);
      } catch (_) {
        // position conversion failed – leave cursor where it is
      }
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
      setStatus(t("st_open_file_first"), true);
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
          setStatus(skipped?.message || t("st_image_fail"), true);
          return;
        }
        const ref = computeInsertRef(selectedPath, created.path);
        insertCallback(getEmbeddedAssetUrl(selectedPath, ref), created.name);
        setStatus(`${t("st_image_added")}: ${created.name}`);
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
    markEditorDirty();
    scheduleMermaidPreviewRender();
    scheduleWysiwygDiagramRender();
  });
  editor.on("focus", rememberEditorSelection);
  editor.on("caretChange", rememberEditorSelection);

  // ── Drag-from-sidebar → editor ────────────────────────────
  // Accepts drags originating from tree rows (dragState is set).
  // Builds a markdown snippet appropriate for the file type and inserts it.

  function buildSidebarDropSnippet(droppedPath) {
    if (!selectedPath) return null;
    const name = droppedPath.split("/").pop();
    const ext = name.includes(".") ? name.split(".").pop().toLowerCase() : "";
    const ref = computeInsertRef(selectedPath, droppedPath);

    if (["png", "jpg", "jpeg", "gif", "webp", "svg", "bmp", "avif", "excalidraw"].includes(ext)) {
      // Embedded image — use the asset proxy URL
      const assetUrl = getEmbeddedAssetUrl(selectedPath, ref);
      const altName = name.replace(/\.[^.]+$/, "");
      return `![${altName}](${assetUrl})`;
    }
    // Everything else (md, pdf, txt, …) — plain markdown link
    return `[${name}](${ref})`;
  }

  // ── JSON Editor (jsoneditor by josdejong) ─────────────────────────────────
  let jsonEditor = null;

  function initJsonEditor() {
    if (jsonEditor) return;
    jsonEditor = new JSONEditor(jsonEditorContainer, {
      mode: "tree",
      modes: ["tree", "form", "code", "preview"],
      mainMenuBar: true,
      navigationBar: true,
      statusBar: true,
      onChange() {
        markEditorDirty();
      },
      onError(err) {
        setStatus(err.toString(), true);
      },
    });
  }

  function showJsonEditorMode() {
    initJsonEditor();
    editorContainer.classList.add("hidden");
    jsonEditorContainer.classList.remove("hidden");
    hidePreview();
    hideUploadStage();
    // hide the WYSIWYG/Markdown toggle — not relevant for JSON
    if (editorModeToggle) editorModeToggle.classList.add("hidden");
  }

  function hideJsonEditorMode() {
    jsonEditorContainer.classList.add("hidden");
    if (editorModeToggle) editorModeToggle.classList.remove("hidden");
  }

  const editorStage = editorContainer.closest(".editor-stage") || editorContainer;

  editorStage.addEventListener("dragover", (event) => {
    if (!dragState || dragState.kind === "directory") return;
    if (!selectedPath || !selectedEditable) return;
    event.preventDefault();
    event.dataTransfer.dropEffect = "link";
    editorStage.classList.add("is-drop-target-link");
  });

  editorStage.addEventListener("dragleave", (event) => {
    // Only clear when truly leaving the stage (not moving over a child)
    if (!editorStage.contains(event.relatedTarget)) {
      editorStage.classList.remove("is-drop-target-link");
    }
  });

  editorStage.addEventListener("drop", (event) => {
    editorStage.classList.remove("is-drop-target-link");
    if (!dragState || dragState.kind === "directory") return;
    if (!selectedPath || !selectedEditable) return;
    event.preventDefault();
    event.stopPropagation();
    const snippet = buildSidebarDropSnippet(dragState.path);
    if (snippet) {
      insertEditorSnippet(snippet);
      scheduleWysiwygDiagramRender();
      scheduleMermaidPreviewRender();
      const name = dragState.path.split("/").pop();
      setStatus(`${t("st_link_inserted")}: ${name}`);
    }
  });

  function closeDiagramToolbarMenu() {
    if (!diagramToolbarMenu) return;
    diagramToolbarMenu.classList.add("hidden");
    diagramToolbarMenu.setAttribute("aria-hidden", "true");
    diagramToolbarTrigger?.setAttribute("aria-expanded", "false");
  }

  function toggleDiagramToolbarMenu() {
    if (!diagramToolbarMenu) return;
    const isHidden = diagramToolbarMenu.classList.contains("hidden");
    if (!isHidden) {
      closeDiagramToolbarMenu();
      return;
    }
    // Menu lives in document.body (outside any zoom context) so
    // getBoundingClientRect() on the trigger gives true viewport coords.
    if (diagramToolbarTrigger) {
      const rect = diagramToolbarTrigger.getBoundingClientRect();
      diagramToolbarMenu.style.top = `${rect.bottom + 4}px`;
      diagramToolbarMenu.style.left = `${rect.left}px`;
    }
    diagramToolbarMenu.classList.remove("hidden");
    diagramToolbarMenu.setAttribute("aria-hidden", "false");
    diagramToolbarTrigger?.setAttribute("aria-expanded", "true");
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
    trigger.setAttribute("aria-label", "Insert diagram");
    trigger.setAttribute("aria-expanded", "false");
    trigger.title = "Insert diagram";
    trigger.innerHTML = `<svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="1" y="2" width="6" height="4" rx="1"/><rect x="9" y="10" width="6" height="4" rx="1"/><polyline points="4,6 4,8 12,8 12,10"/></svg>`;
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
      { type: "mermaid-flowchart", label: "Mermaid Flowchart", message: "Mermaid Flowchart block inserted." },
      { type: "mermaid-sequence", label: "Mermaid Sequence", message: "Mermaid Sequence block inserted." },
      { type: "mermaid-class", label: "Mermaid Class", message: "Mermaid Class block inserted." },
      { type: "plantuml-sequence", label: "PlantUML Sequence", message: "PlantUML block inserted." },
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

    // Append menu to document.body so it's outside any zoom stacking context.
    // position:fixed inside a zoomed ancestor positions relative to that
    // ancestor instead of the viewport — moving it to body avoids that.
    group.append(trigger);
    toolbar.appendChild(group);
    document.body.appendChild(menu);
    diagramToolbarMenu = menu;
    diagramToolbarTrigger = trigger;
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

  // Cache: trimmed mermaid source → rendered SVG innerHTML.
  // Used to immediately restore the previous render when ToastUI rebuilds
  // the preview DOM, eliminating the flash of unstyled/raw text.
  const mermaidSvgCache = new Map();

  function normalizeDiagramLanguage(value) {
    const lang = (value || "").toLowerCase().trim();
    if (lang === "plantuml" || lang === "puml") return "plantuml";
    if (lang === "mermaid") return "mermaid";
    return "";
  }

  // Synchronously restore cached SVGs for any unprocessed .mermaid-diagram
  // elements. Must run in the same task as the DOM mutation so the browser
  // never paints the intermediate "raw text" state.
  function restoreCachedMermaidDiagrams() {
    editorContainer.querySelectorAll(".mermaid-diagram:not([data-processed])").forEach((el) => {
      const code = el.textContent.trim();
      const cached = mermaidSvgCache.get(code);
      if (cached) {
        el.innerHTML = cached;
        el.setAttribute("data-processed", "true");
      }
    });
  }

  function scheduleMermaidPreviewRender() {
    if (currentEditorMode !== "markdown") return;
    clearTimeout(mermaidPreviewTimer);
    mermaidPreviewTimer = setTimeout(async () => {
      const unprocessed = Array.from(
        editorContainer.querySelectorAll(".mermaid-diagram:not([data-processed])")
      );
      if (!unprocessed.length) return;
      // Snapshot source before mermaid mutates the elements
      const codes = unprocessed.map((el) => el.textContent.trim());
      await mermaid.run({ nodes: unprocessed }).catch(() => {});
      // Cache each successfully rendered SVG keyed by its source code
      unprocessed.forEach((el, i) => {
        if (el.getAttribute("data-processed") && el.querySelector("svg")) {
          mermaidSvgCache.set(codes[i], el.innerHTML);
        }
      });
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
    // Restore cached SVGs synchronously (before next paint) to avoid flash
    restoreCachedMermaidDiagrams();
    scheduleMermaidPreviewRender();
    scheduleWysiwygDiagramRender();
  }).observe(editorContainer, { childList: true, subtree: true, characterData: true });

  async function renderWysiwygDiagrams() {
    if (currentEditorMode !== "wysiwyg") return;
    const blocks = editorContainer.querySelectorAll(".toastui-editor-ww-code-block");

    // Grab ProseMirror's internal MutationObserver so we can suppress reconciliation
    // around our synchronous DOM injections (mermaid SVG, classList, appendChild).
    let pmInternalObserver = null;
    for (const b of blocks) {
      const obs = b.pmViewDesc?.spec?.view?.domObserver?.observer;
      if (obs) { pmInternalObserver = obs; break; }
    }

    for (const block of blocks) {
      const lang = normalizeDiagramLanguage(
        block.getAttribute("data-language") ||
        block.querySelector("code")?.getAttribute("data-language") ||
        "",
      );
      const out = block.querySelector(".ww-diagram-out");
      if (!lang) {
        pmInternalObserver?.takeRecords();
        out?.remove();
        block.classList.remove("is-diagram-rendered", "is-source-visible");
        pmInternalObserver?.takeRecords();
        continue;
      }

      const code = (block.querySelector("pre code")?.textContent || block.querySelector("pre")?.textContent || "").trim();
      if (!code) {
        pmInternalObserver?.takeRecords();
        out?.remove();
        block.classList.remove("is-diagram-rendered", "is-source-visible");
        pmInternalObserver?.takeRecords();
        continue;
      }

      let nextOut = out;
      const isNew = !nextOut;
      if (!nextOut) {
        nextOut = document.createElement("div");
        nextOut.className = "ww-diagram-out";
        nextOut.tabIndex = 0;
        nextOut.setAttribute("role", "button");
        nextOut.setAttribute("aria-label", "Click to show or hide diagram code");
        nextOut.addEventListener("click", () => {
          const obs = block.pmViewDesc?.spec?.view?.domObserver?.observer;
          obs?.takeRecords();
          block.classList.toggle("is-source-visible");
          obs?.takeRecords();
        });
        nextOut.addEventListener("keydown", (event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            const obs = block.pmViewDesc?.spec?.view?.domObserver?.observer;
            obs?.takeRecords();
            block.classList.toggle("is-source-visible");
            obs?.takeRecords();
          }
        });
      }

      if (nextOut.dataset.code === code && nextOut.dataset.lang === lang) continue;

      if (lang === "mermaid") {
        // Render in an off-screen element appended to document.body — mermaid needs a
        // DOM-attached node, but body is outside ProseMirror's observed subtree.
        const tempEl = document.createElement("div");
        tempEl.style.cssText = "position:fixed;top:-9999px;left:-9999px;visibility:hidden";
        tempEl.textContent = code;
        document.body.appendChild(tempEl);
        const rendered = await mermaid.run({ nodes: [tempEl] }).then(() => true).catch(() => false);
        const svgHtml = tempEl.innerHTML;
        document.body.removeChild(tempEl);

        // Inject synchronously and immediately clear ProseMirror's pending mutation
        // records so it never reconciles against our foreign DOM additions.
        pmInternalObserver?.takeRecords();
        nextOut.dataset.code = code;
        nextOut.dataset.lang = lang;
        nextOut.innerHTML = rendered ? svgHtml : code;
        if (isNew) block.appendChild(nextOut);
        block.classList.toggle("is-diagram-rendered", rendered);
        if (!rendered) block.classList.add("is-source-visible");
        pmInternalObserver?.takeRecords();
      } else {
        pmInternalObserver?.takeRecords();
        nextOut.dataset.code = code;
        nextOut.dataset.lang = lang;
        nextOut.innerHTML = `<img src="${plantUmlSvgUrl(code)}" class="diagram-plantuml" alt="PlantUML diagram" />`;
        if (isNew) block.appendChild(nextOut);
        block.classList.add("is-diagram-rendered");
        pmInternalObserver?.takeRecords();
      }
    }
  }

  // ── Mode switch button in topbar ──────────────────────────
  function setEditorMode(mode) {
    currentEditorMode = mode;
    editor.changeMode(currentEditorMode);
    editorModeToggle.textContent = t(currentEditorMode === "wysiwyg" ? "wysiwyg_mode" : "markdown_mode");
    editorModeToggle.setAttribute("aria-pressed", String(currentEditorMode === "markdown"));
    if (currentEditorMode === "wysiwyg") scheduleWysiwygDiagramRender();
    else scheduleMermaidPreviewRender();
  }

  editorModeToggle.addEventListener("click", () => {
    setEditorMode(currentEditorMode === "wysiwyg" ? "markdown" : "wysiwyg");
  });

  function clampFontSize(value) {
    return Math.max(12, Math.min(28, Number.parseInt(value, 10) || 16));
  }

  // ── Translations ──────────────────────────────────────────
  const TRANSLATIONS = {
    pl: {
      label_config: "Konfiguracja", settings_title: "Ustawienia",
      label_profiles: "Profile", profile_new: "Nowy profil",
      cancel_edit: "Anuluj edycję", save_profile: "Zapamiętaj",
      save_changes: "Zapisz zmiany", edit: "Edytuj", delete_action: "Usuń",
      profile_hint: "Zapisuje aktualne pola formularza jako profil.",
      editing_profile_prefix: "Edytujesz",
      no_profiles_hint: "Brak zapisanych zestawów. Utwórz pierwszy profil w ustawieniach.",
      no_profiles_list: "Brak zapisanych profili.",
      label_source: "Źródło notatek", source_local: "Lokalny dysk",
      label_notes_dir: "Katalog notatek", browse: "Przeglądaj",
      label_port: "Port", label_user: "Użytkownik",
      label_password: "Hasło", label_remote_path: "Ścieżka zdalna",
      sftp_password_hint: "Hasło przechowywane w lokalnej bazie SQLite.",
      gdrive_connected: "Google Drive: połączono",
      gdrive_disconnected: "Google Drive: brak autoryzacji",
      gdrive_reconnect: "Połącz ponownie", gdrive_authorize: "Autoryzuj Drive",
      gdrive_hint: "Po kliknięciu nastąpi przekierowanie do Google.",
      gdrive_console_hint: "Dodaj do Google Console:",
      label_folder_id: "ID folderu (opcjonalne)",
      gdrive_folder_hint: "Skopiuj ID folderu z URL w Google Drive.",
      label_sort: "Sortowanie", sort_alpha: "Alfabetyczne", sort_manual: "Manualne",
      label_language: "Język interfejsu",
      label_theme: "Motyw", theme_light: "Jasny", theme_dark: "Ciemny",
      label_font_size: "Rozmiar czcionki edytora",
      label_autosave: "Automatyczny zapis",
      autosave_hint: "Zapisuje zmiany po krótkiej pauzie w pisaniu.",
      label_image_upload: "Wstawianie obrazków",
      img_same_dir: "Ten sam katalog co plik MD",
      img_subdir: "Podkatalog o nazwie",
      db_path_label: "Baza SQLite:",
      cancel: "Anuluj", save_settings: "Zapisz ustawienia",
      no_file: "Wybierz notatkę Markdown", no_file_path: "Brak zaznaczonego pliku.",
      selected_file_label: "Wybrany plik",
      wysiwyg_mode: "WYSIWYG", markdown_mode: "Markdown",
      new_dir: "Nowy katalog", new_file_title: "Nowy plik",
      create_dir_hint: "Katalog zostanie utworzony w wybranej lokalizacji.",
      create_file_hint: "Rozszerzenie .md zostanie dodane automatycznie, jeśli go nie podasz.",
      location_prefix: "Lokalizacja", element_prefix: "Element",
      root_dir_label: "katalog główny",
      rename_title: "Zmień nazwę", rename_button: "Zmień nazwę",
      rename_hint: "Podaj nową nazwę. Rozszerzenie .md zostanie dodane automatycznie dla plików Markdown.",
      create_button: "Utwórz",
      no_files_selected: "Nie wybrano jeszcze żadnych plików.",
      upload_files_title: "Upload plików",
      upload_target_prefix: "Docelowy katalog",
      no_subdirs: "Brak podkatalogów w tej lokalizacji.",
      st_open_file_first: "Najpierw otwórz plik Markdown.",
      st_image_fail: "Nie udało się dodać obrazka.",
      st_image_added: "Obraz dodany",
      st_link_inserted: "Wstawiono link do",
      st_profile_name_required: "Podaj nazwę profilu.",
      st_saving_profile: "Zapisuję profil ustawień...",
      st_updating_profile: "Aktualizuję profil ustawień...",
      st_profile_saved: "Profil zapisany",
      st_profile_updated: "Profil zaktualizowany",
      st_deleting_profile: "Usuwam profil",
      st_profile_deleted: "Profil usunięty",
      st_loading_profile: "Ładuję profil",
      st_profile_loaded: "Profil załadowany.",
      st_profile_loaded_prefix: "Załadowano profil",
      st_delete_error: "Błąd usuwania.",
      st_deleted: "Usunięto",
      st_delete_fail: "Błąd połączenia przy usuwaniu.",
      st_showing_only: "Pokazuję tylko",
      st_upload_prepared: "Przygotowano upload do",
      st_preparing_zip: "Przygotowuję archiwum ZIP...",
      st_start_download: "Rozpoczynam pobieranie pliku.",
      st_path_copied: "Ścieżka skopiowana.",
      st_path_copy_fail: "Nie udało się skopiować ścieżki.",
      st_loading_dirs: "Wczytuję katalogi...",
      st_choose_dir: "Możesz wybrać katalog.",
      st_folder_name_required: "Podaj nazwę nowego folderu.",
      st_creating_folder: "Tworzę nowy folder...",
      st_folder_created: "Utworzono folder",
      st_dir_selected: "Katalog wybrany. Zapisz ustawienia, aby go zastosować.",
      st_showing_parent: "Pokazuję katalog nadrzędny.",
      st_back_full_tree: "Wróćono do pełnego drzewa.",
      st_refreshing_tree: "Odświeżam drzewo plików...",
      st_tree_ready: "Drzewo plików gotowe.",
      st_loading_file: "Wczytuję plik...",
      st_file_ready: "Plik gotowy do edycji.",
      st_pdf_preview: "Podgląd PDF gotowy.",
      st_image_preview: "Podgląd obrazu gotowy.",
      st_file_not_editable: "Tego pliku nie można edytować.",
      st_autosave_pending: "Oczekiwanie na automatyczny zapis...",
      st_autosaving: "Zapisywanie automatyczne...",
      st_autosaved: "Zapisano automatycznie.",
      st_saving: "Zapisuję plik...",
      st_saved: "Zmiany zapisane.",
      st_json_invalid_saving_raw: "Niepoprawny JSON — zapisano jako tekst.",
      st_saving_settings: "Zapisuję ustawienia...",
      st_settings_saved: "Ustawienia zapisane.",
      st_updating_font: "Aktualizuję rozmiar czcionki...",
      st_font_saved: "Rozmiar czcionki zapisany.",
      st_name_required: "Podaj nazwę nowego elementu.",
      st_creating: "Tworzę nowy element...",
      st_dir_created_msg: "Katalog utworzony.",
      st_new_name_required: "Podaj nową nazwę.",
      st_renaming: "Zmieniam nazwę...",
      st_renamed: "Zmieniono nazwę na",
      st_no_files_upload: "Najpierw wybierz pliki do uploadu.",
      st_uploading: "Wysyłam pliki...",
      st_files_added: "Dodano", st_files_skipped: "pominięto",
      st_moving: "Przenoszę element...",
      st_moved: "Element przeniesiony.",
      st_updating_order: "Aktualizuję kolejność...",
      st_order_saved: "Kolejność zapisana.",
      st_showing_hidden: "Ukryte pliki są widoczne.",
      st_hiding_hidden: "Ukryte pliki są ukryte.",
    },
    en: {
      label_config: "Configuration", settings_title: "Settings",
      label_profiles: "Profiles", profile_new: "New profile",
      cancel_edit: "Cancel editing", save_profile: "Save",
      save_changes: "Save changes", edit: "Edit", delete_action: "Delete",
      profile_hint: "Saves the current form fields as a quick-switch profile.",
      editing_profile_prefix: "Editing",
      no_profiles_hint: "No saved profiles yet. Create your first profile in settings.",
      no_profiles_list: "No saved profiles.",
      label_source: "Notes source", source_local: "Local disk",
      label_notes_dir: "Notes directory", browse: "Browse",
      label_port: "Port", label_user: "Username",
      label_password: "Password", label_remote_path: "Remote path",
      sftp_password_hint: "Password is stored in the local SQLite database.",
      gdrive_connected: "Google Drive: connected",
      gdrive_disconnected: "Google Drive: not authorized",
      gdrive_reconnect: "Reconnect", gdrive_authorize: "Authorize Drive",
      gdrive_hint: "You will be redirected to Google after clicking.",
      gdrive_console_hint: "Add to Google Console:",
      label_folder_id: "Folder ID (optional)",
      gdrive_folder_hint: "Copy the folder ID from the Google Drive URL.",
      label_sort: "Sorting", sort_alpha: "Alphabetical", sort_manual: "Manual",
      label_language: "Interface language",
      label_theme: "Theme", theme_light: "Light", theme_dark: "Dark",
      label_font_size: "Editor font size",
      label_autosave: "Automatic save",
      autosave_hint: "Saves changes after a short pause while typing.",
      label_image_upload: "Image insertion",
      img_same_dir: "Same directory as MD file",
      img_subdir: "Subdirectory named",
      db_path_label: "SQLite database:",
      cancel: "Cancel", save_settings: "Save settings",
      no_file: "Select a Markdown note", no_file_path: "No file selected.",
      selected_file_label: "Selected file",
      wysiwyg_mode: "WYSIWYG", markdown_mode: "Markdown",
      new_dir: "New directory", new_file_title: "New file",
      create_dir_hint: "The directory will be created at the selected location.",
      create_file_hint: "The .md extension will be added automatically if not provided.",
      location_prefix: "Location", element_prefix: "Item",
      root_dir_label: "root directory",
      rename_title: "Rename", rename_button: "Rename",
      rename_hint: "Enter a new name. The .md extension will be added automatically for Markdown files.",
      create_button: "Create",
      no_files_selected: "No files selected yet.",
      upload_files_title: "Upload files",
      upload_target_prefix: "Target directory",
      no_subdirs: "No subdirectories at this location.",
      st_open_file_first: "Open a Markdown file first.",
      st_image_fail: "Failed to add image.",
      st_image_added: "Image added",
      st_link_inserted: "Link inserted to",
      st_profile_name_required: "Enter a profile name.",
      st_saving_profile: "Saving settings profile...",
      st_updating_profile: "Updating settings profile...",
      st_profile_saved: "Profile saved",
      st_profile_updated: "Profile updated",
      st_deleting_profile: "Deleting profile",
      st_profile_deleted: "Profile deleted",
      st_loading_profile: "Loading profile",
      st_profile_loaded: "Profile loaded.",
      st_profile_loaded_prefix: "Profile loaded",
      st_delete_error: "Delete error.",
      st_deleted: "Deleted",
      st_delete_fail: "Connection error while deleting.",
      st_showing_only: "Showing only",
      st_upload_prepared: "Upload prepared to",
      st_preparing_zip: "Preparing ZIP archive...",
      st_start_download: "Starting file download.",
      st_path_copied: "Path copied.",
      st_path_copy_fail: "Failed to copy path.",
      st_loading_dirs: "Loading directories...",
      st_choose_dir: "You can choose a directory.",
      st_folder_name_required: "Enter a folder name.",
      st_creating_folder: "Creating folder...",
      st_folder_created: "Folder created",
      st_dir_selected: "Directory selected. Save settings to apply.",
      st_showing_parent: "Showing parent directory.",
      st_back_full_tree: "Returned to full tree.",
      st_refreshing_tree: "Refreshing file tree...",
      st_tree_ready: "File tree ready.",
      st_loading_file: "Loading file...",
      st_file_ready: "File ready to edit.",
      st_pdf_preview: "PDF preview ready.",
      st_image_preview: "Image preview ready.",
      st_file_not_editable: "This file cannot be edited.",
      st_autosave_pending: "Waiting to autosave...",
      st_autosaving: "Autosaving...",
      st_autosaved: "Autosaved.",
      st_saving: "Saving file...",
      st_saved: "Changes saved.",
      st_json_invalid_saving_raw: "Invalid JSON — saved as raw text.",
      st_saving_settings: "Saving settings...",
      st_settings_saved: "Settings saved.",
      st_updating_font: "Updating font size...",
      st_font_saved: "Font size saved.",
      st_name_required: "Enter a name for the new item.",
      st_creating: "Creating item...",
      st_dir_created_msg: "Directory created.",
      st_new_name_required: "Enter a new name.",
      st_renaming: "Renaming...",
      st_renamed: "Renamed to",
      st_no_files_upload: "Select files to upload first.",
      st_uploading: "Uploading files...",
      st_files_added: "Added", st_files_skipped: "skipped",
      st_moving: "Moving item...",
      st_moved: "Item moved.",
      st_updating_order: "Updating order...",
      st_order_saved: "Order saved.",
      st_showing_hidden: "Hidden files are visible.",
      st_hiding_hidden: "Hidden files are hidden.",
    },
    es: {
      label_config: "Configuración", settings_title: "Configuración",
      label_profiles: "Perfiles", profile_new: "Nuevo perfil",
      cancel_edit: "Cancelar edición", save_profile: "Guardar",
      save_changes: "Guardar cambios", edit: "Editar", delete_action: "Eliminar",
      profile_hint: "Guarda los campos actuales como perfil de cambio rápido.",
      editing_profile_prefix: "Editando",
      no_profiles_hint: "No hay perfiles guardados. Crea el primero en los ajustes.",
      no_profiles_list: "No hay perfiles guardados.",
      label_source: "Fuente de notas", source_local: "Disco local",
      label_notes_dir: "Directorio de notas", browse: "Explorar",
      label_port: "Puerto", label_user: "Usuario",
      label_password: "Contraseña", label_remote_path: "Ruta remota",
      sftp_password_hint: "La contraseña se almacena en la base de datos SQLite local.",
      gdrive_connected: "Google Drive: conectado",
      gdrive_disconnected: "Google Drive: no autorizado",
      gdrive_reconnect: "Reconectar", gdrive_authorize: "Autorizar Drive",
      gdrive_hint: "Serás redirigido a Google al hacer clic.",
      gdrive_console_hint: "Añadir a Google Console:",
      label_folder_id: "ID de carpeta (opcional)",
      gdrive_folder_hint: "Copia el ID de la carpeta desde la URL de Google Drive.",
      label_sort: "Ordenación", sort_alpha: "Alfabético", sort_manual: "Manual",
      label_language: "Idioma de la interfaz",
      label_theme: "Tema", theme_light: "Claro", theme_dark: "Oscuro",
      label_font_size: "Tamaño de fuente del editor",
      label_autosave: "Guardado automático",
      autosave_hint: "Guarda los cambios tras una breve pausa al escribir.",
      label_image_upload: "Inserción de imágenes",
      img_same_dir: "Mismo directorio que el archivo MD",
      img_subdir: "Subdirectorio llamado",
      db_path_label: "Base de datos SQLite:",
      cancel: "Cancelar", save_settings: "Guardar configuración",
      no_file: "Selecciona una nota Markdown", no_file_path: "Ningún archivo seleccionado.",
      selected_file_label: "Archivo seleccionado",
      wysiwyg_mode: "WYSIWYG", markdown_mode: "Markdown",
      new_dir: "Nuevo directorio", new_file_title: "Nuevo archivo",
      create_dir_hint: "El directorio se creará en la ubicación seleccionada.",
      create_file_hint: "La extensión .md se añadirá automáticamente si no se indica.",
      location_prefix: "Ubicación", element_prefix: "Elemento",
      root_dir_label: "directorio raíz",
      rename_title: "Renombrar", rename_button: "Renombrar",
      rename_hint: "Introduce un nuevo nombre. La extensión .md se añadirá automáticamente para archivos Markdown.",
      create_button: "Crear",
      no_files_selected: "Aún no se han seleccionado archivos.",
      upload_files_title: "Subir archivos",
      upload_target_prefix: "Directorio de destino",
      no_subdirs: "No hay subdirectorios en esta ubicación.",
      st_open_file_first: "Abre primero un archivo Markdown.",
      st_image_fail: "No se pudo añadir la imagen.",
      st_image_added: "Imagen añadida",
      st_link_inserted: "Enlace insertado a",
      st_profile_name_required: "Introduce un nombre de perfil.",
      st_saving_profile: "Guardando perfil de ajustes...",
      st_updating_profile: "Actualizando perfil de ajustes...",
      st_profile_saved: "Perfil guardado",
      st_profile_updated: "Perfil actualizado",
      st_deleting_profile: "Eliminando perfil",
      st_profile_deleted: "Perfil eliminado",
      st_loading_profile: "Cargando perfil",
      st_profile_loaded: "Perfil cargado.",
      st_profile_loaded_prefix: "Perfil cargado",
      st_delete_error: "Error al eliminar.",
      st_deleted: "Eliminado",
      st_delete_fail: "Error de conexión al eliminar.",
      st_showing_only: "Mostrando solo",
      st_upload_prepared: "Subida preparada a",
      st_preparing_zip: "Preparando archivo ZIP...",
      st_start_download: "Iniciando descarga del archivo.",
      st_path_copied: "Ruta copiada.",
      st_path_copy_fail: "No se pudo copiar la ruta.",
      st_loading_dirs: "Cargando directorios...",
      st_choose_dir: "Puedes elegir un directorio.",
      st_folder_name_required: "Introduce un nombre de carpeta.",
      st_creating_folder: "Creando carpeta...",
      st_folder_created: "Carpeta creada",
      st_dir_selected: "Directorio seleccionado. Guarda los ajustes para aplicarlo.",
      st_showing_parent: "Mostrando directorio padre.",
      st_back_full_tree: "Vuelto al árbol completo.",
      st_refreshing_tree: "Actualizando árbol de archivos...",
      st_tree_ready: "Árbol de archivos listo.",
      st_loading_file: "Cargando archivo...",
      st_file_ready: "Archivo listo para editar.",
      st_pdf_preview: "Vista previa PDF lista.",
      st_image_preview: "Vista previa de imagen lista.",
      st_file_not_editable: "Este archivo no se puede editar.",
      st_autosave_pending: "Esperando para guardar automáticamente...",
      st_autosaving: "Guardando automáticamente...",
      st_autosaved: "Guardado automáticamente.",
      st_saving: "Guardando archivo...",
      st_saved: "Cambios guardados.",
      st_json_invalid_saving_raw: "JSON inválido — guardado como texto.",
      st_saving_settings: "Guardando ajustes...",
      st_settings_saved: "Ajustes guardados.",
      st_updating_font: "Actualizando tamaño de fuente...",
      st_font_saved: "Tamaño de fuente guardado.",
      st_name_required: "Introduce un nombre para el nuevo elemento.",
      st_creating: "Creando elemento...",
      st_dir_created_msg: "Directorio creado.",
      st_new_name_required: "Introduce un nuevo nombre.",
      st_renaming: "Renombrando...",
      st_renamed: "Renombrado a",
      st_no_files_upload: "Selecciona primero los archivos para subir.",
      st_uploading: "Subiendo archivos...",
      st_files_added: "Añadidos", st_files_skipped: "omitidos",
      st_moving: "Moviendo elemento...",
      st_moved: "Elemento movido.",
      st_updating_order: "Actualizando orden...",
      st_order_saved: "Orden guardado.",
      st_showing_hidden: "Los archivos ocultos son visibles.",
      st_hiding_hidden: "Los archivos ocultos están ocultos.",
    },
    de: {
      label_config: "Konfiguration", settings_title: "Einstellungen",
      label_profiles: "Profile", profile_new: "Neues Profil",
      cancel_edit: "Bearbeitung abbrechen", save_profile: "Speichern",
      save_changes: "Änderungen speichern", edit: "Bearbeiten", delete_action: "Löschen",
      profile_hint: "Speichert die aktuellen Felder als Schnellwechsel-Profil.",
      editing_profile_prefix: "Bearbeitung von",
      no_profiles_hint: "Keine gespeicherten Profile. Erstelle das erste Profil in den Einstellungen.",
      no_profiles_list: "Keine gespeicherten Profile.",
      label_source: "Notizenquelle", source_local: "Lokale Festplatte",
      label_notes_dir: "Notizenverzeichnis", browse: "Durchsuchen",
      label_port: "Port", label_user: "Benutzer",
      label_password: "Passwort", label_remote_path: "Remotepfad",
      sftp_password_hint: "Passwort wird in der lokalen SQLite-Datenbank gespeichert.",
      gdrive_connected: "Google Drive: verbunden",
      gdrive_disconnected: "Google Drive: nicht autorisiert",
      gdrive_reconnect: "Erneut verbinden", gdrive_authorize: "Drive autorisieren",
      gdrive_hint: "Nach dem Klicken werden Sie zu Google weitergeleitet.",
      gdrive_console_hint: "Zur Google Console hinzufügen:",
      label_folder_id: "Ordner-ID (optional)",
      gdrive_folder_hint: "Kopieren Sie die Ordner-ID aus der Google Drive URL.",
      label_sort: "Sortierung", sort_alpha: "Alphabetisch", sort_manual: "Manuell",
      label_language: "Oberflächensprache",
      label_theme: "Design", theme_light: "Hell", theme_dark: "Dunkel",
      label_font_size: "Editorschriftgröße",
      label_autosave: "Automatisch speichern",
      autosave_hint: "Speichert Änderungen nach einer kurzen Schreibpause.",
      label_image_upload: "Bildeinfügung",
      img_same_dir: "Gleiches Verzeichnis wie MD-Datei",
      img_subdir: "Unterverzeichnis namens",
      db_path_label: "SQLite-Datenbank:",
      cancel: "Abbrechen", save_settings: "Einstellungen speichern",
      no_file: "Markdown-Notiz auswählen", no_file_path: "Keine Datei ausgewählt.",
      selected_file_label: "Ausgewählte Datei",
      wysiwyg_mode: "WYSIWYG", markdown_mode: "Markdown",
      new_dir: "Neues Verzeichnis", new_file_title: "Neue Datei",
      create_dir_hint: "Das Verzeichnis wird am gewählten Ort erstellt.",
      create_file_hint: "Die Erweiterung .md wird automatisch hinzugefügt, wenn sie nicht angegeben wird.",
      location_prefix: "Ort", element_prefix: "Element",
      root_dir_label: "Stammverzeichnis",
      rename_title: "Umbenennen", rename_button: "Umbenennen",
      rename_hint: "Neuen Namen eingeben. Die Erweiterung .md wird für Markdown-Dateien automatisch ergänzt.",
      create_button: "Erstellen",
      no_files_selected: "Noch keine Dateien ausgewählt.",
      upload_files_title: "Dateien hochladen",
      upload_target_prefix: "Zielverzeichnis",
      no_subdirs: "Keine Unterverzeichnisse an diesem Ort.",
      st_open_file_first: "Bitte zuerst eine Markdown-Datei öffnen.",
      st_image_fail: "Bild konnte nicht hinzugefügt werden.",
      st_image_added: "Bild hinzugefügt",
      st_link_inserted: "Link eingefügt zu",
      st_profile_name_required: "Profilnamen eingeben.",
      st_saving_profile: "Einstellungsprofil wird gespeichert...",
      st_updating_profile: "Einstellungsprofil wird aktualisiert...",
      st_profile_saved: "Profil gespeichert",
      st_profile_updated: "Profil aktualisiert",
      st_deleting_profile: "Profil wird gelöscht",
      st_profile_deleted: "Profil gelöscht",
      st_loading_profile: "Profil wird geladen",
      st_profile_loaded: "Profil geladen.",
      st_profile_loaded_prefix: "Profil geladen",
      st_delete_error: "Fehler beim Löschen.",
      st_deleted: "Gelöscht",
      st_delete_fail: "Verbindungsfehler beim Löschen.",
      st_showing_only: "Zeige nur",
      st_upload_prepared: "Upload vorbereitet nach",
      st_preparing_zip: "ZIP-Archiv wird vorbereitet...",
      st_start_download: "Dateidownload wird gestartet.",
      st_path_copied: "Pfad kopiert.",
      st_path_copy_fail: "Pfad konnte nicht kopiert werden.",
      st_loading_dirs: "Verzeichnisse werden geladen...",
      st_choose_dir: "Sie können ein Verzeichnis auswählen.",
      st_folder_name_required: "Ordnernamen eingeben.",
      st_creating_folder: "Ordner wird erstellt...",
      st_folder_created: "Ordner erstellt",
      st_dir_selected: "Verzeichnis ausgewählt. Einstellungen speichern, um anzuwenden.",
      st_showing_parent: "Übergeordnetes Verzeichnis wird angezeigt.",
      st_back_full_tree: "Zurück zum vollständigen Baum.",
      st_refreshing_tree: "Dateibaum wird aktualisiert...",
      st_tree_ready: "Dateibaum bereit.",
      st_loading_file: "Datei wird geladen...",
      st_file_ready: "Datei bereit zur Bearbeitung.",
      st_pdf_preview: "PDF-Vorschau bereit.",
      st_image_preview: "Bildvorschau bereit.",
      st_file_not_editable: "Diese Datei kann nicht bearbeitet werden.",
      st_autosave_pending: "Warten auf automatisches Speichern...",
      st_autosaving: "Automatisches Speichern...",
      st_autosaved: "Automatisch gespeichert.",
      st_saving: "Datei wird gespeichert...",
      st_saved: "Änderungen gespeichert.",
      st_json_invalid_saving_raw: "Ungültiges JSON — als Text gespeichert.",
      st_saving_settings: "Einstellungen werden gespeichert...",
      st_settings_saved: "Einstellungen gespeichert.",
      st_updating_font: "Schriftgröße wird aktualisiert...",
      st_font_saved: "Schriftgröße gespeichert.",
      st_name_required: "Namen für das neue Element eingeben.",
      st_creating: "Element wird erstellt...",
      st_dir_created_msg: "Verzeichnis erstellt.",
      st_new_name_required: "Neuen Namen eingeben.",
      st_renaming: "Umbenennen...",
      st_renamed: "Umbenannt zu",
      st_no_files_upload: "Zuerst Dateien zum Hochladen auswählen.",
      st_uploading: "Dateien werden hochgeladen...",
      st_files_added: "Hinzugefügt", st_files_skipped: "übersprungen",
      st_moving: "Element wird verschoben...",
      st_moved: "Element verschoben.",
      st_updating_order: "Reihenfolge wird aktualisiert...",
      st_order_saved: "Reihenfolge gespeichert.",
      st_showing_hidden: "Versteckte Dateien sind sichtbar.",
      st_hiding_hidden: "Versteckte Dateien sind ausgeblendet.",
    },
    ru: {
      label_config: "Конфигурация", settings_title: "Настройки",
      label_profiles: "Профили", profile_new: "Новый профиль",
      cancel_edit: "Отмена редактирования", save_profile: "Сохранить",
      save_changes: "Сохранить изменения", edit: "Редактировать", delete_action: "Удалить",
      profile_hint: "Сохраняет текущие поля как профиль быстрого переключения.",
      editing_profile_prefix: "Редактирование",
      no_profiles_hint: "Нет сохранённых профилей. Создайте первый профиль в настройках.",
      no_profiles_list: "Нет сохранённых профилей.",
      label_source: "Источник заметок", source_local: "Локальный диск",
      label_notes_dir: "Каталог заметок", browse: "Обзор",
      label_port: "Порт", label_user: "Пользователь",
      label_password: "Пароль", label_remote_path: "Удалённый путь",
      sftp_password_hint: "Пароль хранится в локальной базе данных SQLite.",
      gdrive_connected: "Google Drive: подключён",
      gdrive_disconnected: "Google Drive: нет авторизации",
      gdrive_reconnect: "Переподключить", gdrive_authorize: "Авторизовать Drive",
      gdrive_hint: "После нажатия вы будете перенаправлены в Google.",
      gdrive_console_hint: "Добавить в Google Console:",
      label_folder_id: "ID папки (необязательно)",
      gdrive_folder_hint: "Скопируйте ID папки из URL Google Drive.",
      label_sort: "Сортировка", sort_alpha: "Алфавитная", sort_manual: "Ручная",
      label_language: "Язык интерфейса",
      label_theme: "Тема", theme_light: "Светлая", theme_dark: "Тёмная",
      label_font_size: "Размер шрифта редактора",
      label_autosave: "Автосохранение",
      autosave_hint: "Сохраняет изменения после короткой паузы при вводе.",
      label_image_upload: "Вставка изображений",
      img_same_dir: "Тот же каталог, что и MD-файл",
      img_subdir: "Подкаталог с именем",
      db_path_label: "База данных SQLite:",
      cancel: "Отмена", save_settings: "Сохранить настройки",
      no_file: "Выберите заметку Markdown", no_file_path: "Файл не выбран.",
      selected_file_label: "Выбранный файл",
      wysiwyg_mode: "WYSIWYG", markdown_mode: "Markdown",
      new_dir: "Новый каталог", new_file_title: "Новый файл",
      create_dir_hint: "Каталог будет создан в выбранном месте.",
      create_file_hint: "Расширение .md будет добавлено автоматически, если не указано.",
      location_prefix: "Расположение", element_prefix: "Элемент",
      root_dir_label: "корневой каталог",
      rename_title: "Переименовать", rename_button: "Переименовать",
      rename_hint: "Введите новое имя. Расширение .md будет добавлено автоматически для файлов Markdown.",
      create_button: "Создать",
      no_files_selected: "Файлы ещё не выбраны.",
      upload_files_title: "Загрузка файлов",
      upload_target_prefix: "Целевой каталог",
      no_subdirs: "Подкаталогов в этом расположении нет.",
      st_open_file_first: "Сначала откройте файл Markdown.",
      st_image_fail: "Не удалось добавить изображение.",
      st_image_added: "Изображение добавлено",
      st_link_inserted: "Ссылка вставлена на",
      st_profile_name_required: "Введите имя профиля.",
      st_saving_profile: "Сохранение профиля настроек...",
      st_updating_profile: "Обновление профиля настроек...",
      st_profile_saved: "Профиль сохранён",
      st_profile_updated: "Профиль обновлён",
      st_deleting_profile: "Удаление профиля",
      st_profile_deleted: "Профиль удалён",
      st_loading_profile: "Загрузка профиля",
      st_profile_loaded: "Профиль загружен.",
      st_profile_loaded_prefix: "Профиль загружен",
      st_delete_error: "Ошибка удаления.",
      st_deleted: "Удалено",
      st_delete_fail: "Ошибка соединения при удалении.",
      st_showing_only: "Показывается только",
      st_upload_prepared: "Загрузка подготовлена в",
      st_preparing_zip: "Подготовка ZIP-архива...",
      st_start_download: "Начало загрузки файла.",
      st_path_copied: "Путь скопирован.",
      st_path_copy_fail: "Не удалось скопировать путь.",
      st_loading_dirs: "Загрузка каталогов...",
      st_choose_dir: "Можно выбрать каталог.",
      st_folder_name_required: "Введите имя новой папки.",
      st_creating_folder: "Создание папки...",
      st_folder_created: "Папка создана",
      st_dir_selected: "Каталог выбран. Сохраните настройки, чтобы применить.",
      st_showing_parent: "Показывается родительский каталог.",
      st_back_full_tree: "Возврат к полному дереву.",
      st_refreshing_tree: "Обновление дерева файлов...",
      st_tree_ready: "Дерево файлов готово.",
      st_loading_file: "Загрузка файла...",
      st_file_ready: "Файл готов к редактированию.",
      st_pdf_preview: "Предпросмотр PDF готов.",
      st_image_preview: "Предпросмотр изображения готов.",
      st_file_not_editable: "Этот файл нельзя редактировать.",
      st_autosave_pending: "Ожидание автосохранения...",
      st_autosaving: "Автосохранение...",
      st_autosaved: "Автоматически сохранено.",
      st_saving: "Сохранение файла...",
      st_saved: "Изменения сохранены.",
      st_json_invalid_saving_raw: "Неверный JSON — сохранено как текст.",
      st_saving_settings: "Сохранение настроек...",
      st_settings_saved: "Настройки сохранены.",
      st_updating_font: "Обновление размера шрифта...",
      st_font_saved: "Размер шрифта сохранён.",
      st_name_required: "Введите имя нового элемента.",
      st_creating: "Создание элемента...",
      st_dir_created_msg: "Каталог создан.",
      st_new_name_required: "Введите новое имя.",
      st_renaming: "Переименование...",
      st_renamed: "Переименовано в",
      st_no_files_upload: "Сначала выберите файлы для загрузки.",
      st_uploading: "Загрузка файлов...",
      st_files_added: "Добавлено", st_files_skipped: "пропущено",
      st_moving: "Перемещение элемента...",
      st_moved: "Элемент перемещён.",
      st_updating_order: "Обновление порядка...",
      st_order_saved: "Порядок сохранён.",
      st_showing_hidden: "Скрытые файлы видны.",
      st_hiding_hidden: "Скрытые файлы скрыты.",
    },
  };

  function applyLanguage(lang) {
    const t = TRANSLATIONS[lang] || TRANSLATIONS.pl;
    document.documentElement.lang = lang;
    shell.dataset.language = lang;

    // Translate all [data-i18n] elements
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.dataset.i18n;
      if (t[key] !== undefined) el.textContent = t[key];
    });

    // Translate <option> elements with [data-i18n-opt]
    document.querySelectorAll("[data-i18n-opt]").forEach((el) => {
      const key = el.dataset.i18nOpt;
      if (t[key] !== undefined) el.textContent = t[key];
    });

    // Update dynamic text nodes that are set by JS
    if (currentFileLabel && !selectedPath) {
      currentFileLabel.textContent = t.no_file;
    }
    if (currentFilePath && !selectedPath) {
      currentFilePath.textContent = t.no_file_path;
    }
    if (editorModeToggle) {
      const modeKey = currentEditorMode === "wysiwyg" ? "wysiwyg_mode" : "markdown_mode";
      editorModeToggle.textContent = t[modeKey] || editorModeToggle.textContent;
    }
  }

  function t(key) {
    const lang = preferences?.language || shell?.dataset?.language || "pl";
    return (TRANSLATIONS[lang] || TRANSLATIONS.pl)[key] || key;
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
    createTitle.textContent = kind === "directory" ? t("new_dir") : t("new_file_title");
    createHint.textContent = kind === "directory" ? t("create_dir_hint") : t("create_file_hint");
    createParentLabel.textContent = `${t("location_prefix")}: ${parentPath || t("root_dir_label")}`;
    createNameInput.value = "";
    createModal.classList.remove("hidden");
    createModal.setAttribute("aria-hidden", "false");
    window.setTimeout(() => createNameInput.focus(), 0);
  }

  function openRenameModal(node) {
    modalAction = "rename";
    renameTargetNode = node;
    createTitle.textContent = t("rename_title");
    createHint.textContent = t("rename_hint");
    createParentLabel.textContent = `${t("element_prefix")}: ${node.path || node.name}`;
    createNameInput.value = node.name;
    confirmCreateButton.textContent = t("rename_button");
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
    confirmCreateButton.textContent = t("create_button");
  }

  function setStatus(message, isError = false, kind = "") {
    statusMessage.textContent = message;
    statusMessage.style.color = isError ? "#9a3412" : "";
    statusMessage.classList.toggle("status-autosaving", kind === "autosaving");
  }

  function toggleOverlay({ empty = false, unsupported = false }) {
    emptyState.classList.toggle("hidden", !empty);
    unsupportedState.classList.toggle("hidden", !unsupported);
  }

  function updateHeader(name, path) {
    currentFileLabel.textContent = name || t("no_file");
    currentFilePath.textContent = path || t("no_file_path");
  }

  function applyHiddenFilesToggleState() {
    toggleHiddenFilesButton.classList.toggle("is-active", showHiddenFiles);
    toggleHiddenFilesButton.setAttribute("aria-pressed", String(showHiddenFiles));
    toggleHiddenFilesButton.setAttribute(
      "aria-label",
      showHiddenFiles ? "Hide hidden files" : "Show hidden files",
    );
    toggleHiddenFilesButton.title = showHiddenFiles ? "Hide hidden files" : "Show hidden files";
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
    hideJsonEditorMode();
    hidePreview();
    hideUploadStage();
    if (editorModeToggle) editorModeToggle.classList.remove("hidden");
  }

  function showPreviewMode(file) {
    editorContainer.classList.add("hidden");
    hideJsonEditorMode();
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
    hideJsonEditorMode();
    hidePreview();
    hideUploadStage();
  }

  function getUploadTargetLabel(path) {
    return path || t("root_dir_label");
  }

  function renderUploadFileList() {
    uploadFileList.innerHTML = "";
    if (!pendingUploadFiles.length) {
      const empty = document.createElement("div");
      empty.className = "upload-file-empty muted";
      empty.textContent = t("no_files_selected");
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
    updateHeader(t("upload_files_title"), getUploadTargetLabel(uploadTargetPath));
    uploadTargetLabel.textContent = `${t("upload_target_prefix")}: ${getUploadTargetLabel(uploadTargetPath)}`;
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
      let detail = t("st_delete_error");
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
      let detail = t("st_delete_error");
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
      autosave_enabled: Boolean(autosaveEnabledInput?.checked),
      image_upload_mode: imageUploadModeSelect?.value || "same_dir",
      image_upload_subdir: imageUploadSubdirInput?.value?.trim() || "assets",
      language: languageSelect?.value || "pl",
      ...overrides,
    };
  }

  function applyPreferencesToForm(nextPreferences) {
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
    if (autosaveEnabledInput) autosaveEnabledInput.checked = Boolean(nextPreferences.autosave_enabled);
    if (imageUploadModeSelect) imageUploadModeSelect.value = nextPreferences.image_upload_mode || "same_dir";
    if (imageUploadSubdirInput) imageUploadSubdirInput.value = nextPreferences.image_upload_subdir || "assets";
    if (imageUploadSubdirSection) imageUploadSubdirSection.classList.toggle("hidden", nextPreferences.image_upload_mode !== "subdir");
    if (languageSelect) languageSelect.value = nextPreferences.language || "pl";
    applySourceTypeVisibility(nextPreferences.source_type || "local");
    profileFormGdriveCredentials = nextPreferences.gdrive_credentials || "";
  }

  function applyPreferencesToUi(nextPreferences) {
    preferences = nextPreferences;
    applyPreferencesToForm(nextPreferences);
    contentRootDisplay.textContent = preferences.content_root;
    applyTheme(preferences.theme_mode);
    applyEditorFontSize(preferences.editor_font_size);
    applyLanguage(preferences.language || "pl");
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
    if (profileEditorTitle) profileEditorTitle.textContent = t("profile_new");
    if (saveProfileButton) saveProfileButton.textContent = t("save_profile");
    cancelProfileEditButton?.classList.add("hidden");
    if (profileNameInput) profileNameInput.value = "";
    if (resetForm && preferences) {
      applyPreferencesToForm(preferences);
    }
    renderSettingsPreferenceProfiles();
  }

  function startProfileEditing(profile) {
    editingPreferenceProfileId = profile.id;
    if (profileEditorTitle) profileEditorTitle.textContent = `${t("editing_profile_prefix")}: ${profile.name}`;
    if (saveProfileButton) saveProfileButton.textContent = t("save_changes");
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
      empty.textContent = t("no_profiles_hint");
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
      empty.textContent = t("no_profiles_list");
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
      editButton.textContent = t("edit");
      editButton.addEventListener("click", () => startProfileEditing(profile));

      const deleteButton = document.createElement("button");
      deleteButton.type = "button";
      deleteButton.className = "button button-secondary settings-profile-action";
      deleteButton.textContent = t("delete_action");
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
      setStatus(t("st_profile_name_required"), true);
      profileNameInput?.focus();
      return;
    }

    try {
      const isEditing = editingPreferenceProfileId !== null;
      setStatus(isEditing ? t("st_updating_profile") : t("st_saving_profile"));
      const url = isEditing ? `${config.preferenceProfilesUrl}/${editingPreferenceProfileId}` : config.preferenceProfilesUrl;
      const method = isEditing ? "PUT" : "POST";
      const profile = await requestJson(url, {
        method,
        body: JSON.stringify(buildProfilePayload({ name: profileName })),
      });
      await loadPreferenceProfiles();
      resetProfileEditor();
      setStatus(isEditing ? `${t("st_profile_updated")}: ${profile.name}.` : `${t("st_profile_saved")}: ${profile.name}.`);
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  async function deletePreferenceProfile(profile) {
    if (!window.confirm(`Delete profile "${profile.name}"?`)) {
      return;
    }

    try {
      setStatus(`${t("st_deleting_profile")}: ${profile.name}...`);
      await requestJson(`${config.preferenceProfilesUrl}/${profile.id}`, {
        method: "DELETE",
      });
      if (editingPreferenceProfileId === profile.id) {
        resetProfileEditor({ resetForm: true });
      }
      await loadPreferenceProfiles();
      setStatus(`${t("st_profile_deleted")}: ${profile.name}.`);
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  async function resetWorkspaceAfterPreferencesChange() {
    clearAutosaveTimer();
    editorDirty = false;
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
      setStatus(`${t("st_loading_profile")}${profileName ? `: ${profileName}` : ""}...`);
      const nextPreferences = await requestJson(`${config.preferenceProfilesUrl}/${profileId}/apply`, {
        method: "POST",
      });
      applyPreferencesToUi(nextPreferences);
      closePreferenceProfilesDropdown();
      await resetWorkspaceAfterPreferencesChange();
      setStatus(profileName ? `${t("st_profile_loaded_prefix")}: ${profileName}.` : t("st_profile_loaded"));
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
        setStatus(data.detail || t("st_delete_error"), true);
        return;
      }
      if (selectedTreePath === node.path) {
        selectedTreePath = "";
        selectedTreeKind = "directory";
        toggleOverlay({ empty: true });
      }
      await loadTree();
      setStatus(`${t("st_deleted")}: ${node.name}.`);
    } catch {
      setStatus(t("st_delete_fail"), true);
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
        createContextMenuButton(expandedDirectories.has(node.path) ? "Collapse" : "Expand", async () => {
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
        createContextMenuButton("Scope to this folder", async () => {
          setScopedRoot(node.path);
          setStatus(`${t("st_showing_only")} ${node.path}.`);
        }),
      );
    } else {
      treeContextMenu.appendChild(
        createContextMenuButton("Open", async () => {
          await loadFile(node.path);
        }),
      );
    }

    treeContextMenu.appendChild(
      createContextMenuButton("Upload here", async () => {
        showUploadMode(uploadPath);
        setStatus(`${t("st_upload_prepared")} ${getUploadTargetLabel(uploadPath)}.`);
      }),
    );
    treeContextMenu.appendChild(
      createContextMenuButton("New file here", async () => {
        openCreateModal("file", parentPath);
      }),
    );
    treeContextMenu.appendChild(
      createContextMenuButton("New directory here", async () => {
        openCreateModal("directory", parentPath);
      }),
    );
    treeContextMenu.appendChild(
      createContextMenuButton(node.kind === "directory" ? "Download as ZIP" : "Download", async () => {
        window.location.href = `${config.downloadUrl}?path=${encodeURIComponent(node.path)}`;
        setStatus(node.kind === "directory" ? t("st_preparing_zip") : t("st_start_download"));
      }),
    );
    treeContextMenu.appendChild(
      createContextMenuButton("Copy path", async () => {
        try {
          await navigator.clipboard.writeText(node.path);
          setStatus(t("st_path_copied"));
        } catch (error) {
          setStatus(t("st_path_copy_fail"), true);
        }
      }),
    );
    treeContextMenu.appendChild(
      createContextMenuButton("Rename", async () => {
        openRenameModal(node);
      }),
    );
    treeContextMenu.appendChild(
      createContextMenuButton("Refresh tree", async () => {
        await loadTree();
      }, "muted"),
    );

    const isConfirming = contextMenuState.deleteConfirm === true;
    treeContextMenu.appendChild(
      createContextMenuButton(
        isConfirming ? "Click again to confirm" : "Delete",
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

  /**
   * Add touch long-press to trigger the context menu (tablet support).
   * A press held for ≥ 500 ms without moving fires the menu at the touch point.
   * Moving the finger or lifting it early cancels the timer.
   */
  function addLongPressContextMenu(element, node) {
    let timer = null;
    let startX = 0;
    let startY = 0;

    element.addEventListener("touchstart", (e) => {
      if (e.touches.length !== 1) return;
      const touch = e.touches[0];
      startX = touch.clientX;
      startY = touch.clientY;
      timer = setTimeout(() => {
        timer = null;
        // Prevent the subsequent click / contextmenu from firing twice
        element.addEventListener("touchend", (te) => te.preventDefault(), { once: true });
        openTreeContextMenu(
          { preventDefault() {}, clientX: startX, clientY: startY },
          node,
        );
      }, 500);
    }, { passive: true });

    const cancel = () => { if (timer) { clearTimeout(timer); timer = null; } };
    element.addEventListener("touchend",    cancel, { passive: true });
    element.addEventListener("touchcancel", cancel, { passive: true });
    element.addEventListener("touchmove", (e) => {
      // Cancel if finger moved more than 10 px (user is scrolling)
      const t = e.touches[0];
      if (Math.abs(t.clientX - startX) > 10 || Math.abs(t.clientY - startY) > 10) cancel();
    }, { passive: true });
  }

  function renderDirectoryBrowser(payload) {
    directoryBrowserState = payload;
    renderDirectoryBrowserPath(payload.current_path);
    directoryBrowserList.innerHTML = "";
    directoryBrowserUpButton.disabled = !payload.parent_path;

    if (!payload.directories.length) {
      const empty = document.createElement("div");
      empty.className = "directory-browser-empty muted";
      empty.textContent = t("no_subdirs");
      directoryBrowserList.appendChild(empty);
      return;
    }

    payload.directories.forEach((directory) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "directory-browser-item";
      button.innerHTML = `<svg class="directory-browser-item-icon" width="15" height="15" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true"><path d="M1.5 3.5A1.5 1.5 0 0 1 3 2h3.586a1.5 1.5 0 0 1 1.06.44l.915.914A1.5 1.5 0 0 0 9.62 3.8H13a1.5 1.5 0 0 1 1.5 1.5v7A1.5 1.5 0 0 1 13 13.8H3A1.5 1.5 0 0 1 1.5 12.3V3.5Z"/></svg><span class="directory-browser-item-name">${directory.name}</span><svg class="directory-browser-item-chevron" width="12" height="12" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="6,4 10,8 6,12"/></svg>`;
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
      setStatus(t("st_loading_dirs"));
      openDirectoryBrowserModal();
      const startPath = contentRootInput.value.trim();
      await loadDirectoryBrowser(startPath);
      toggleDirectoryCreate(false);
      setStatus(t("st_choose_dir"));
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
      setStatus(t("st_folder_name_required"), true);
      directoryBrowserCreateInput?.focus();
      return;
    }

    try {
      setStatus(t("st_creating_folder"));
      const payload = await requestJson(config.createDirectoryUrl, {
        method: "POST",
        body: JSON.stringify({
          parent_path: directoryBrowserState.current_path,
          name,
        }),
      });
      renderDirectoryBrowser(payload);
      toggleDirectoryCreate(false);
      setStatus(`${t("st_folder_created")}: ${name}.`);
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
    setStatus(t("st_dir_selected"));
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
      addLongPressContextMenu(row, node);
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
    addLongPressContextMenu(row, node);
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
      upButton.title = "Go up";
      upButton.addEventListener("click", () => {
        const parentPath = getParentPath(visibleNode.path);
        setScopedRoot(parentPath);
        setStatus(parentPath ? t("st_showing_parent") : t("st_back_full_tree"));
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
    setStatus(t("st_refreshing_tree"));
    treeData = await requestJson(config.treeUrl, { method: "GET" });
    if (scopedRootPath && !findDirectoryNode(treeData, scopedRootPath)) {
      scopedRootPath = "";
      applyTreeScopeState();
    }
    renderTree(treeData);
    setStatus(t("st_tree_ready"));

    if (autoSelect && !selectedPath) {
      const firstEditable = findFirstEditable(treeData);
      if (firstEditable) {
        await loadFile(firstEditable);
      }
    }
  }

  async function loadFile(path) {
    try {
      if (selectedPath && selectedPath !== path) {
        await flushAutosave();
      }
      setStatus(t("st_loading_file"));
      const file = await requestJson(`${config.fileUrl}?path=${encodeURIComponent(path)}`, {
        method: "GET",
      });

      isApplyingDocument = true;
      selectedPath = file.path;
      selectedEditable = file.editable;
      selectedFileType = file.file_type || "markdown";
      selectedTreePath = file.path;
      selectedTreeKind = "file";
      openParentDirectories(file.path);
      updateHeader(file.name, file.path);
      saveButton.disabled = !file.editable;

      if (file.editable && selectedFileType === "json") {
        showJsonEditorMode();
        try {
          jsonEditor.set(JSON.parse(file.content || "{}"));
        } catch {
          // invalid JSON on disk — fall back to text mode so user can fix it
          jsonEditor.setText(file.content || "");
          jsonEditor.setMode("code");
        }
        toggleOverlay({ empty: false, unsupported: false });
        setStatus(t("st_file_ready"));
      } else if (file.editable) {
        showEditorMode();
        if (selectedFileType === "text" && currentEditorMode !== "markdown") {
          setEditorMode("markdown");
        }
        editor.setMarkdown(file.content || "", false);
        setTimeout(renderWysiwygDiagrams, 200);
        toggleOverlay({ empty: false, unsupported: false });
        setStatus(t("st_file_ready"));
      } else if (file.previewable) {
        showPreviewMode(file);
        editor.setMarkdown("", false);
        toggleOverlay({ empty: false, unsupported: false });
        setStatus(file.preview_kind === "pdf" ? t("st_pdf_preview") : t("st_image_preview"));
      } else {
        showUnsupportedMode();
        editor.setMarkdown("", false);
        toggleOverlay({ empty: false, unsupported: true });
        setStatus(file.message || t("st_file_not_editable"));
      }

      editorDirty = false;
      clearAutosaveTimer();
      isApplyingDocument = false;
      renderTree(treeData);
    } catch (error) {
      isApplyingDocument = false;
      setStatus(error.message, true);
    }
  }

  function isAutosaveEnabled() {
    return Boolean(preferences?.autosave_enabled);
  }

  function clearAutosaveTimer() {
    if (!autosaveTimer) return;
    clearTimeout(autosaveTimer);
    autosaveTimer = null;
  }

  function markEditorDirty() {
    if (isApplyingDocument || !selectedPath || !selectedEditable) return;
    editorDirty = true;
    scheduleAutosave();
  }

  function getCurrentEditorContent() {
    if (selectedFileType === "json") {
      try {
        return JSON.stringify(jsonEditor.get(), null, 2);
      } catch {
        return jsonEditor.getText();
      }
    }
    if (selectedFileType === "text") {
      return editor.getMarkdown();
    }
    return cleanEmbeddedUrls(editor.getMarkdown());
  }

  function scheduleAutosave() {
    clearAutosaveTimer();
    if (!isAutosaveEnabled() || !selectedPath || !selectedEditable || !editorDirty) return;
    setStatus(t("st_autosave_pending"), false, "autosaving");
    const scheduledPath = selectedPath;
    autosaveTimer = setTimeout(() => {
      autosaveTimer = null;
      if (selectedPath !== scheduledPath || !editorDirty) return;
      saveFile({ automatic: true });
    }, AUTOSAVE_DELAY_MS);
  }

  async function flushAutosave() {
    if (!isAutosaveEnabled() || !editorDirty || !selectedPath || !selectedEditable) return;
    clearAutosaveTimer();
    await saveFile({ automatic: true });
  }

  async function saveFile({ automatic = false } = {}) {
    if (!selectedPath || !selectedEditable) {
      return;
    }

    if (automatic && autosaveInFlight) {
      autosaveQueued = true;
      return;
    }

    try {
      clearAutosaveTimer();
      autosaveInFlight = automatic;
      setStatus(automatic ? t("st_autosaving") : t("st_saving"), false, automatic ? "autosaving" : "");

      const savedPath = selectedPath;
      const content = getCurrentEditorContent();
      if (selectedFileType === "json") {
        try {
          JSON.parse(content);
        } catch {
          setStatus(t("st_json_invalid_saving_raw"), true);
        }
      }

      await requestJson(config.saveUrl, {
        method: "PUT",
        body: JSON.stringify({ path: savedPath, content }),
      });
      if (selectedPath === savedPath) {
        editorDirty = getCurrentEditorContent() !== content;
      }
      toggleOverlay({ empty: false, unsupported: false });
      setStatus(automatic ? t("st_autosaved") : t("st_saved"));
      if (!automatic) {
        await loadTree();
      }
    } catch (error) {
      setStatus(error.message, true);
    } finally {
      if (automatic) {
        autosaveInFlight = false;
        if (autosaveQueued) {
          autosaveQueued = false;
          scheduleAutosave();
        }
      }
    }
  }

  async function saveSettings() {
    try {
      setStatus(t("st_saving_settings"));
      await persistPreferences();
      closeSettingsModal();
      await resetWorkspaceAfterPreferencesChange();
      setStatus(t("st_settings_saved"));
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  async function adjustEditorFontSize(delta) {
    const nextSize = clampFontSize((preferences?.editor_font_size || 16) + delta);
    try {
      setStatus(t("st_updating_font"));
      await persistPreferences({ editor_font_size: nextSize });
      setStatus(t("st_font_saved"));
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  async function createItem() {
    const parentPath = createParentPathOverride ?? getCurrentParentPath();
    const name = createNameInput.value.trim();
    if (!name) {
      setStatus(t("st_name_required"), true);
      createNameInput.focus();
      return;
    }

    try {
      setStatus(t("st_creating"));
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
        setStatus(t("st_dir_created_msg"));
      }
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  async function renameItem() {
    const node = renameTargetNode;
    const newName = createNameInput.value.trim();
    if (!newName) {
      setStatus(t("st_new_name_required"), true);
      createNameInput.focus();
      return;
    }
    try {
      setStatus(t("st_renaming"));
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
      setStatus(`${t("st_renamed")}: ${renamed.name}.`);
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
      setStatus(t("st_no_files_upload"), true);
      return;
    }

    try {
      setStatus(t("st_uploading"));
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
        const firstMessage = result.skipped_items[0]?.message || "";
        setStatus(`${t("st_files_added")} ${createdCount}, ${t("st_files_skipped")} ${skippedCount}.${firstMessage ? " " + firstMessage : ""}`, true);
      } else {
        setStatus(`${t("st_files_added")} ${createdCount}.`);
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
      setStatus(t("st_moving"));
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
        setStatus(t("st_moved"));
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
      setStatus(t("st_updating_order"));
      preferences = await requestJson(config.orderUrl, {
        method: "PUT",
        body: JSON.stringify({
          parent_path: parentPath,
          ordered_paths: orderedPaths,
        }),
      });
      await loadTree();
      setStatus(t("st_order_saved"));
    } catch (error) {
      setStatus(error.message, true);
    }
  }

  refreshButton.addEventListener("click", () => {
    loadTree();
  });
  resetTreeRootButton.addEventListener("click", () => {
    setScopedRoot("");
    setStatus(t("st_back_full_tree"));
  });
  toggleHiddenFilesButton.addEventListener("click", () => {
    showHiddenFiles = !showHiddenFiles;
    applyHiddenFilesToggleState();
    renderTree(treeData);
    setStatus(showHiddenFiles ? t("st_showing_hidden") : t("st_hiding_hidden"));
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
  applyLanguage(shell.dataset.language || "pl");
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

// ---------------------------------------------------------------------------
// PWA — service worker registration
// ---------------------------------------------------------------------------

// PWA temporarily DISABLED for debugging layout issues.
// Actively unregister any previously-installed SW and purge its caches so that
// the browser stops serving stale assets. Once unregistered, the next reload
// goes straight to the network — no manual DevTools dance needed.
if ("serviceWorker" in navigator) {
  window.addEventListener("load", async () => {
    try {
      const regs = await navigator.serviceWorker.getRegistrations();
      let hadAny = false;
      for (const reg of regs) {
        hadAny = true;
        await reg.unregister();
      }
      if (window.caches && caches.keys) {
        const keys = await caches.keys();
        await Promise.all(keys.map((k) => caches.delete(k)));
      }
      if (hadAny) {
        console.warn("Service worker unregistered + caches cleared — reloading once.");
        // one-shot reload so the now-uncontrolled page fetches fresh assets
        if (!sessionStorage.getItem("sw-nuked")) {
          sessionStorage.setItem("sw-nuked", "1");
          window.location.reload();
        }
      }
    } catch (err) {
      console.warn("SW cleanup failed:", err);
    }
  });
}
