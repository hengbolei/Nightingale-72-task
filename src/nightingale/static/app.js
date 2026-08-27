import {
  ApiError,
  DEMO_CONTEXT,
  addComment,
  addTimelineEntry,
  createHighlight,
  getAuditEvents,
  getPatientDetail,
  getSectionRevisions,
  revertSection,
  setDemoRole,
  setCommentResolved,
  updateHighlight,
  updateSection,
} from "/static/api.js";

const elements = {
  name: document.querySelector("#patient-name"),
  pronouns: document.querySelector("#patient-pronouns"),
  mrn: document.querySelector("#patient-mrn"),
  dob: document.querySelector("#patient-dob"),
  content: document.querySelector("#patient-content"),
  highlightList: document.querySelector("#highlight-list"),
  highlightCount: document.querySelector("#highlight-count"),
  timelineList: document.querySelector("#timeline-list"),
  entryCount: document.querySelector("#entry-count"),
  patientHeader: document.querySelector("#patient-header"),
  screenState: document.querySelector("#screen-state"),
  stateTitle: document.querySelector("#state-title"),
  stateMessage: document.querySelector("#state-message"),
  retryButton: document.querySelector("#retry-button"),
  sectionContent: document.querySelector("#section-content"),
  sectionVersion: document.querySelector("#section-version"),
  saveSection: document.querySelector("#save-section"),
  showHistory: document.querySelector("#show-history"),
  sectionFeedback: document.querySelector("#section-feedback"),
  revisionList: document.querySelector("#revision-list"),
  commentContent: document.querySelector("#comment-content"),
  commentAssignee: document.querySelector("#comment-assignee"),
  addComment: document.querySelector("#add-comment"),
  commentFeedback: document.querySelector("#comment-feedback"),
  commentList: document.querySelector("#comment-list"),
  commentCount: document.querySelector("#comment-count"),
  staffNoteCard: document.querySelector("#staff-note-card"),
  entryTitle: document.querySelector("#entry-title"),
  entryContent: document.querySelector("#entry-content"),
  addEntry: document.querySelector("#add-entry"),
  entryFeedback: document.querySelector("#entry-feedback"),
  highlightComposerCard: document.querySelector("#highlight-composer-card"),
  selectedSource: document.querySelector("#selected-source"),
  highlightReason: document.querySelector("#highlight-reason"),
  highlightAction: document.querySelector("#highlight-action"),
  highlightPatientInstruction: document.querySelector("#highlight-patient-instruction"),
  highlightPriority: document.querySelector("#highlight-priority"),
  highlightStatus: document.querySelector("#highlight-status"),
  highlightAssignee: document.querySelector("#highlight-assignee"),
  createHighlight: document.querySelector("#create-highlight"),
  highlightCreateFeedback: document.querySelector("#highlight-create-feedback"),
  auditList: document.querySelector("#audit-list"),
  auditCount: document.querySelector("#audit-count"),
  patientDashboard: document.querySelector("#patient-dashboard"),
  patientActionList: document.querySelector("#patient-action-list"),
  patientActionCount: document.querySelector("#patient-action-count"),
  patientEntryTitle: document.querySelector("#patient-entry-title"),
  patientEntryContent: document.querySelector("#patient-entry-content"),
  addPatientEntry: document.querySelector("#add-patient-entry"),
  patientEntryFeedback: document.querySelector("#patient-entry-feedback"),
  demoRole: document.querySelector("#demo-role"),
  glancePanel: document.querySelector("#glance-panel"),
  workspacePanel: document.querySelector("#workspace-panel"),
};

let currentPlanVersion = 0;
let replyToCommentId = null;
let selectedHighlightSource = null;

const screenStates = {
  loading: ["Loading longitudinal record", "Securely retrieving patient details, priorities, and timeline."],
  empty: ["No longitudinal record yet", "This patient has no visible priority items or timeline entries."],
  forbidden: ["Access denied", "Your current identity cannot view this patient record. Check your role and clinic scope."],
  notFound: ["Patient record not found", "This patient does not exist or is not visible within your clinic scope."],
  error: ["Unable to load the record", "The service could not be reached. Please try again."],
};

const statusLabels = {
  ai_suggested: "AI suggested · Unconfirmed",
  clinician_confirmed: "Clinician confirmed",
  needs_review: "Needs review",
  rejected: "Rejected",
};

const entryTypeLabels = {
  patient_note: "Patient note",
  staff_note: "Staff note",
  clinician_note: "Clinician note",
  ai_doctor_consult_summary: "AI doctor consult summary",
  ai_nurse_consult_summary: "AI nurse consult summary",
  ai_patient_session_summary: "AI patient session summary",
  system_event: "System event",
};

const roleLabels = {
  patient: "Patient",
  staff: "Staff",
  clinician: "Clinician",
  admin: "Admin",
  system: "AI / System",
};

const actionStatusLabels = {
  open: "Open",
  in_progress: "In progress",
  completed: "Completed",
};

function createElement(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function setScreenState(state) {
  if (state === "ready") {
    elements.screenState.hidden = true;
    elements.content.hidden = false;
    elements.patientHeader.setAttribute("aria-busy", "false");
    return;
  }
  const [title, message] = screenStates[state];
  elements.screenState.hidden = false;
  elements.screenState.className = `screen-state ${state}`;
  elements.screenState.dataset.state = state;
  elements.stateTitle.textContent = title;
  elements.stateMessage.textContent = message;
  elements.retryButton.hidden = !["error", "notFound"].includes(state);
  elements.content.hidden = true;
  elements.patientHeader.setAttribute("aria-busy", String(state === "loading"));
}

function clearPatient() {
  elements.name.textContent = "Patient record";
  elements.pronouns.textContent = "—";
  elements.mrn.textContent = "—";
  elements.dob.textContent = "—";
  elements.highlightList.replaceChildren();
  elements.timelineList.replaceChildren();
}

function formatDate(value) {
  return new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
  }).format(new Date(`${value}T00:00:00`));
}

function formatDateTime(value) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date(value));
}

function renderPatient(patient) {
  elements.name.textContent = patient.display_name;
  elements.pronouns.textContent = patient.pronouns || "Pronouns not provided";
  elements.mrn.textContent = patient.medical_record_number;
  elements.dob.textContent = formatDate(patient.date_of_birth);
}

function renderPatientActions(actions) {
  elements.patientActionList.replaceChildren();
  elements.patientActionCount.textContent = `${actions.length} confirmed item${actions.length === 1 ? "" : "s"}`;
  if (actions.length === 0) {
    elements.patientActionList.append(
      createElement(
        "p",
        "helper-text",
        "Your care team has not published any new guidance yet.",
      ),
    );
    return;
  }
  actions.forEach((action) => {
    const item = createElement("article", `patient-action ${action.action_status}`);
    item.append(
      createElement("p", "patient-action-title", action.title),
      createElement("p", "patient-action-instruction", action.instruction),
      createElement(
        "span",
        "patient-action-status",
        actionStatusLabels[action.action_status] || action.action_status,
      ),
    );
    elements.patientActionList.append(item);
  });
}

function renderHighlights(highlights) {
  elements.highlightList.replaceChildren();
  elements.highlightCount.textContent = `${highlights.length} priority item${highlights.length === 1 ? "" : "s"}`;
  highlights.forEach((highlight, index) => {
    const card = createElement(
      "article",
      `highlight-card priority-${index + 1} action-${highlight.action_status}`,
    );
    const priority = createElement(
      "div",
      "priority-marker",
      String(index + 1).padStart(2, "0"),
    );
    const body = createElement("div", "highlight-body");
    const top = createElement("div", "highlight-topline");
    top.append(
      createElement("span", `status-chip ${highlight.status}`, statusLabels[highlight.status]),
      createElement("span", "priority-score", `Priority ${highlight.priority}`),
    );
    body.append(
      top,
      createElement("h3", "highlight-text", highlight.text),
      createElement("p", "risk-reason", highlight.risk_reason),
    );
    const footer = createElement("div", "highlight-footer");
    const action = createElement("p", "suggested-action");
    action.append(
      createElement("span", "action-label", "Suggested action"),
      document.createTextNode(highlight.suggested_action),
    );
    const sourceButton = createElement("button", "text-button", "View exact source");
    sourceButton.type = "button";
    const openSource = () => {
      const target = document.querySelector(`#source-${highlight.id}`)
        || document.querySelector(`#entry-${highlight.provenance_pointer.entry_id}`);
      if (!target) return;
      document.querySelectorAll(".source-target").forEach((node) => {
        node.classList.remove("source-target");
      });
      target.classList.add("source-target");
      target.scrollIntoView({ behavior: "smooth", block: "center" });
    };
    sourceButton.addEventListener("click", openSource);
    footer.append(action, sourceButton);

    const controls = createElement("div", "highlight-controls");
    const reviewSelect = createSelect(
      "Review status",
      statusLabels,
      highlight.status,
      `review-${highlight.id}`,
    );
    if (DEMO_CONTEXT.actorRole === "staff") {
      [...reviewSelect.select.options].forEach((option) => {
        option.disabled = ["clinician_confirmed", "rejected"].includes(option.value);
      });
    }
    const assignmentSelect = createSelect(
      "Assigned to",
      { "": "Unassigned", staff: "Staff", clinician: "Clinician", admin: "Admin" },
      highlight.assigned_to || "",
      `assignee-${highlight.id}`,
    );
    const actionSelect = createSelect(
      "Action status",
      actionStatusLabels,
      highlight.action_status,
      `action-${highlight.id}`,
    );
    controls.append(reviewSelect.wrapper, assignmentSelect.wrapper, actionSelect.wrapper);

    const noteLabel = createElement("label", "field-label", "Disposition note");
    noteLabel.htmlFor = `note-${highlight.id}`;
    const note = createElement("textarea", "highlight-note");
    note.id = `note-${highlight.id}`;
    note.rows = 2;
    note.maxLength = 1000;
    note.value = highlight.disposition_note || "";
    const save = createElement("button", "primary-button", "Save update");
    save.type = "button";
    const feedback = createElement("span", "form-feedback");
    save.addEventListener("click", async () => {
      save.disabled = true;
      showFeedback(feedback, "Saving…");
      try {
        await updateHighlight(highlight.id, {
          expected_version: highlight.version,
          status: reviewSelect.select.value,
          assigned_to: assignmentSelect.select.value || null,
          action_status: actionSelect.select.value,
          disposition_note: note.value.trim() || null,
        });
        await loadPatient();
      } catch (error) {
        showFeedback(feedback, error.message, true);
        save.disabled = false;
      }
    });
    const updateActions = createElement("div", "highlight-update-actions");
    updateActions.append(save, feedback);
    body.append(footer, controls, noteLabel, note, updateActions);
    card.append(priority, body);
    elements.highlightList.append(card);
  });
}

function createSelect(label, options, selectedValue, id) {
  const wrapper = createElement("label", "compact-field");
  const labelText = createElement("span", "field-label", label);
  const select = createElement("select");
  select.id = id;
  Object.entries(options).forEach(([value, text]) => {
    const option = createElement("option", "", text);
    option.value = value;
    option.selected = value === selectedValue;
    select.append(option);
  });
  wrapper.append(labelText, select);
  return { wrapper, select };
}

function appendEntryContent(container, entry, highlights) {
  const pointers = highlights
    .filter((highlight) => highlight.provenance_pointer.entry_id === entry.id)
    .sort((left, right) => left.provenance_pointer.start - right.provenance_pointer.start);
  let cursor = 0;
  pointers.forEach((highlight) => {
    const { start, end } = highlight.provenance_pointer;
    if (start < cursor || end > entry.content.length) return;
    container.append(document.createTextNode(entry.content.slice(cursor, start)));
    const mark = createElement("mark", "provenance-mark", entry.content.slice(start, end));
    mark.id = `source-${highlight.id}`;
    container.append(mark);
    cursor = end;
  });
  container.append(document.createTextNode(entry.content.slice(cursor)));
}

function useSelectedTimelineText(entry, content) {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0 || selection.isCollapsed) {
    showFeedback(
      elements.highlightCreateFeedback,
      "Select a phrase in this entry first.",
      true,
    );
    return;
  }
  const range = selection.getRangeAt(0);
  if (!content.contains(range.startContainer) || !content.contains(range.endContainer)) {
    showFeedback(
      elements.highlightCreateFeedback,
      "The selection must stay within one timeline entry.",
      true,
    );
    return;
  }
  const before = document.createRange();
  before.selectNodeContents(content);
  before.setEnd(range.startContainer, range.startOffset);
  const start = before.toString().length;
  const text = range.toString();
  selectedHighlightSource = {
    entryId: entry.id,
    start,
    end: start + text.length,
    text,
  };
  elements.selectedSource.textContent = `“${text}” — ${entry.title}`;
  elements.createHighlight.disabled = false;
  showFeedback(elements.highlightCreateFeedback, "Source captured. Complete the fields below.");
  elements.highlightComposerCard.scrollIntoView({ behavior: "smooth", block: "center" });
}

function renderTimeline(entries, highlights) {
  elements.timelineList.replaceChildren();
  elements.entryCount.textContent = `${entries.length} timeline entr${entries.length === 1 ? "y" : "ies"}`;
  entries.forEach((entry) => {
    const item = createElement(
      "article",
      `timeline-entry role-${entry.author_role} type-${entry.type}`,
    );
    item.id = `entry-${entry.id}`;
    const rail = createElement("div", "timeline-rail");
    rail.append(createElement("span", "timeline-dot"));
    const card = createElement("div", "entry-card");
    const meta = createElement("div", "entry-meta");
    meta.append(
      createElement("span", "entry-type", entryTypeLabels[entry.type] || entry.type),
      createElement("span", "entry-role", roleLabels[entry.author_role] || entry.author_role),
      createElement("time", "entry-time", formatDateTime(entry.timestamp)),
    );
    card.append(meta, createElement("h3", "entry-title", entry.title));
    if (entry.type.startsWith("ai_")) {
      card.append(
        createElement(
          "p",
          "ai-disclaimer",
          "AI-generated content · Review against the original session; not clinically confirmed",
        ),
      );
    }
    const content = createElement("p", "entry-content");
    appendEntryContent(content, entry, highlights);
    card.append(content);
    const footer = createElement("div", "entry-footer");
    footer.append(
      createElement("span", "origin-label", `Source: ${entry.origin.source_label}`),
    );
    if (entry.review_status) {
      footer.append(
        createElement(
          "span",
          `status-chip ${entry.review_status}`,
          statusLabels[entry.review_status],
        ),
      );
    }
    if (DEMO_CONTEXT.actorRole === "clinician") {
      const selectButton = createElement(
        "button",
        "text-button entry-selection-action",
        "Use selected text",
      );
      selectButton.type = "button";
      selectButton.addEventListener("mousedown", (event) => event.preventDefault());
      selectButton.addEventListener("click", () => useSelectedTimelineText(entry, content));
      footer.append(selectButton);
    }
    card.append(footer);
    item.append(rail, card);
    elements.timelineList.append(item);
  });
}

function renderAudit(events) {
  elements.auditList.replaceChildren();
  elements.auditCount.textContent = `${events.length} event${events.length === 1 ? "" : "s"}`;
  if (events.length === 0) {
    elements.auditList.append(
      createElement("p", "helper-text", "No audited changes in this session yet."),
    );
    return;
  }
  [...events].reverse().forEach((event) => {
    const item = createElement("article", "audit-item");
    item.append(
      createElement(
        "span",
        "audit-operation",
        `${event.operation.replaceAll("_", " ")} · ${event.resource} v${event.version}`,
      ),
      createElement("span", "audit-actor", `Actor ${event.changed_by}`),
      createElement("time", "", formatDateTime(event.changed_at)),
    );
    elements.auditList.append(item);
  });
}

function renderSection(sections) {
  const plan = sections.find((section) => section.section === "plan");
  currentPlanVersion = plan?.version || 0;
  elements.sectionContent.value = plan?.content || "";
  elements.sectionVersion.textContent = `Version ${currentPlanVersion}`;
}

function renderComments(comments) {
  elements.commentList.replaceChildren();
  elements.commentCount.textContent = `${comments.length} comment${comments.length === 1 ? "" : "s"}`;
  comments.forEach((comment) => {
    const item = createElement(
      "article",
      `comment-item${comment.resolved ? " resolved" : ""}${comment.parent_id ? " reply" : ""}`,
    );
    const meta = createElement("div", "comment-meta");
    meta.append(
      createElement(
        "span",
        "",
        `${roleLabels[comment.author_role] || comment.author_role} · ${formatDateTime(comment.created_at)}`,
      ),
    );
    const toggle = createElement(
      "button",
      "text-button",
      comment.resolved ? "Reopen" : "Resolve",
    );
    toggle.type = "button";
    toggle.addEventListener("click", async () => {
      try {
        await setCommentResolved(comment.id, !comment.resolved);
        await loadPatient();
      } catch (error) {
        showFeedback(elements.commentFeedback, error.message, true);
      }
    });
    const reply = createElement("button", "text-button", "Reply");
    reply.type = "button";
    reply.addEventListener("click", () => {
      replyToCommentId = comment.id;
      elements.commentContent.focus();
      showFeedback(elements.commentFeedback, "Your next comment will be added as a reply.");
    });
    const controls = createElement("span", "comment-controls");
    controls.append(reply, toggle);
    meta.append(controls);
    item.append(meta, createElement("p", "comment-content", comment.content));
    comment.mentions.forEach((mention) => {
      item.append(createElement("span", "mention-chip", `@${mention}`));
    });
    if (comment.assigned_to) {
      item.append(
        createElement("span", "assignment-chip", `Assigned: ${comment.assigned_to}`),
      );
    }
    elements.commentList.append(item);
  });
}

function showFeedback(element, message, isError = false) {
  element.textContent = message;
  element.classList.toggle("error", isError);
}

async function renderHistory() {
  try {
    const revisions = await getSectionRevisions("plan");
    elements.revisionList.replaceChildren();
    [...revisions].reverse().forEach((revision, index) => {
      const item = createElement("article", "revision-item");
      const meta = createElement("div", "revision-meta");
      meta.append(
        createElement(
          "span",
          "",
          `Version ${revision.version} · ${revision.operation} · ${formatDateTime(revision.changed_at)}`,
        ),
      );
      if (index > 0) {
        const button = createElement("button", "text-button", "Revert to this");
        button.type = "button";
        button.addEventListener("click", async () => {
          try {
            await revertSection("plan", revision.version);
            showFeedback(elements.sectionFeedback, `Reverted to version ${revision.version}.`);
            await loadPatient();
            await renderHistory();
          } catch (error) {
            showFeedback(elements.sectionFeedback, error.message, true);
          }
        });
        meta.append(button);
      }
      item.append(meta, createElement("p", "revision-content", revision.content));
      if (revision.diff) {
        item.append(createElement("pre", "revision-diff", revision.diff));
      }
      elements.revisionList.append(item);
    });
  } catch (error) {
    showFeedback(elements.sectionFeedback, error.message, true);
  }
}

async function loadPatient() {
  setScreenState("loading");
  try {
    const detail = await getPatientDetail();
    renderPatient(detail.patient);
    renderHighlights(detail.highlights);
    renderTimeline(detail.entries, detail.highlights);
    renderSection(detail.sections || []);
    renderComments(detail.comments || []);
    renderPatientActions(detail.patient_actions || []);
    const isPatient = DEMO_CONTEXT.actorRole === "patient";
    if (!isPatient) {
      try {
        renderAudit(await getAuditEvents());
      } catch (error) {
        renderAudit([]);
        console.error("Audit request failed", error);
      }
    }
    elements.glancePanel.hidden = isPatient;
    elements.patientDashboard.hidden = !isPatient;
    elements.workspacePanel.hidden = isPatient;
    elements.staffNoteCard.hidden = DEMO_CONTEXT.actorRole !== "staff";
    elements.highlightComposerCard.hidden = DEMO_CONTEXT.actorRole !== "clinician";
    elements.sectionContent.disabled = DEMO_CONTEXT.actorRole !== "clinician";
    elements.saveSection.disabled = DEMO_CONTEXT.actorRole !== "clinician";
    const isEmpty = detail.highlights.length === 0 && detail.entries.length === 0;
    setScreenState(isEmpty ? "empty" : "ready");
    return detail;
  } catch (error) {
    clearPatient();
    if (error instanceof ApiError && error.status === 403) {
      setScreenState("forbidden");
    } else if (error instanceof ApiError && error.status === 404) {
      setScreenState("notFound");
    } else {
      setScreenState("error");
    }
    console.error("Patient detail request failed", error);
    return null;
  }
}

elements.retryButton.addEventListener("click", loadPatient);
elements.demoRole.addEventListener("change", () => {
  setDemoRole(elements.demoRole.value);
  selectedHighlightSource = null;
  elements.selectedSource.textContent = "No source text selected.";
  elements.createHighlight.disabled = true;
  loadPatient();
});
elements.addEntry.addEventListener("click", async () => {
  const title = elements.entryTitle.value.trim();
  const content = elements.entryContent.value.trim();
  if (!title || !content) {
    showFeedback(elements.entryFeedback, "Enter both a title and note content.", true);
    return;
  }
  elements.addEntry.disabled = true;
  showFeedback(elements.entryFeedback, "Adding note…");
  try {
    await addTimelineEntry(title, content);
    elements.entryTitle.value = "";
    elements.entryContent.value = "";
    await loadPatient();
    showFeedback(elements.entryFeedback, "Staff note added to the timeline.");
  } catch (error) {
    showFeedback(elements.entryFeedback, error.message, true);
  } finally {
    elements.addEntry.disabled = false;
  }
});
elements.addPatientEntry.addEventListener("click", async () => {
  const title = elements.patientEntryTitle.value.trim();
  const content = elements.patientEntryContent.value.trim();
  if (!title || !content) {
    showFeedback(
      elements.patientEntryFeedback,
      "Enter both a title and an update for your care team.",
      true,
    );
    return;
  }
  elements.addPatientEntry.disabled = true;
  showFeedback(elements.patientEntryFeedback, "Sharing update…");
  try {
    await addTimelineEntry(title, content);
    elements.patientEntryTitle.value = "";
    elements.patientEntryContent.value = "";
    await loadPatient();
    showFeedback(elements.patientEntryFeedback, "Your update was added to the timeline.");
  } catch (error) {
    showFeedback(elements.patientEntryFeedback, error.message, true);
  } finally {
    elements.addPatientEntry.disabled = false;
  }
});
elements.createHighlight.addEventListener("click", async () => {
  const reason = elements.highlightReason.value.trim();
  const action = elements.highlightAction.value.trim();
  if (!selectedHighlightSource || !reason || !action) {
    showFeedback(
      elements.highlightCreateFeedback,
      "Select source text and enter a risk reason and suggested action.",
      true,
    );
    return;
  }
  elements.createHighlight.disabled = true;
  showFeedback(elements.highlightCreateFeedback, "Creating highlight…");
  try {
    await createHighlight({
      entry_id: selectedHighlightSource.entryId,
      start: selectedHighlightSource.start,
      end: selectedHighlightSource.end,
      risk_reason: reason,
      suggested_action: action,
      patient_instruction: elements.highlightPatientInstruction.value.trim() || null,
      priority: Number(elements.highlightPriority.value),
      status: elements.highlightStatus.value,
      assigned_to: elements.highlightAssignee.value || null,
    });
    selectedHighlightSource = null;
    elements.selectedSource.textContent = "No source text selected.";
    elements.highlightReason.value = "";
    elements.highlightAction.value = "";
    elements.highlightPatientInstruction.value = "";
    await loadPatient();
    showFeedback(elements.highlightCreateFeedback, "Highlight created and audited.");
  } catch (error) {
    showFeedback(elements.highlightCreateFeedback, error.message, true);
    elements.createHighlight.disabled = false;
  }
});
elements.saveSection.addEventListener("click", async () => {
  showFeedback(elements.sectionFeedback, "Saving…");
  try {
    const section = await updateSection(
      "plan",
      elements.sectionContent.value,
      currentPlanVersion,
    );
    currentPlanVersion = section.version;
    elements.sectionVersion.textContent = `Version ${section.version}`;
    showFeedback(elements.sectionFeedback, `Saved version ${section.version}.`);
    await renderHistory();
  } catch (error) {
    showFeedback(elements.sectionFeedback, error.message, true);
  }
});
elements.showHistory.addEventListener("click", renderHistory);
elements.addComment.addEventListener("click", async () => {
  const content = elements.commentContent.value.trim();
  if (!content) {
    showFeedback(elements.commentFeedback, "Enter a comment first.", true);
    return;
  }
  try {
    await addComment(content, elements.commentAssignee.value, replyToCommentId);
    replyToCommentId = null;
    elements.commentContent.value = "";
    elements.commentAssignee.value = "";
    showFeedback(elements.commentFeedback, "Comment added.");
    await loadPatient();
  } catch (error) {
    showFeedback(elements.commentFeedback, error.message, true);
  }
});
loadPatient();
