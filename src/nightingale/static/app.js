import { ApiError, getPatientDetail } from "/static/api.js";

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
};

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

function renderHighlights(highlights) {
  elements.highlightList.replaceChildren();
  elements.highlightCount.textContent = `${highlights.length} priority item${highlights.length === 1 ? "" : "s"}`;
  highlights.forEach((highlight, index) => {
    const card = createElement("article", `highlight-card priority-${index + 1}`);
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
    footer.append(
      action,
      createElement(
        "span",
        "source-label",
        `Source · ${highlight.provenance_pointer.entry_id.slice(0, 8)}`,
      ),
    );
    body.append(footer);
    card.append(priority, body);
    elements.highlightList.append(card);
  });
}

function renderTimeline(entries) {
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
    card.append(createElement("p", "entry-content", entry.content));
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
    card.append(footer);
    item.append(rail, card);
    elements.timelineList.append(item);
  });
}

async function loadPatient() {
  setScreenState("loading");
  try {
    const detail = await getPatientDetail();
    renderPatient(detail.patient);
    renderHighlights(detail.highlights);
    renderTimeline(detail.entries);
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
loadPatient();
