export const DEMO_IDENTITIES = Object.freeze({
  clinician: "40000000-0000-4000-8000-000000000001",
  staff: "30000000-0000-4000-8000-000000000001",
  patient: "20000000-0000-4000-8000-000000000001",
});

export const DEMO_CONTEXT = {
  patientId: "20000000-0000-4000-8000-000000000001",
  actorId: DEMO_IDENTITIES.clinician,
  actorRole: "clinician",
  clinicId: "10000000-0000-4000-8000-000000000001",
};

export function setDemoRole(role) {
  if (!(role in DEMO_IDENTITIES)) throw new Error("Unknown demo role");
  DEMO_CONTEXT.actorRole = role;
  DEMO_CONTEXT.actorId = DEMO_IDENTITIES[role];
}

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function getPatientDetail(context = DEMO_CONTEXT) {
  return request(`/api/patients/${context.patientId}`, {}, context);
}

function authHeaders(context) {
  return {
    "x-actor-id": context.actorId,
    "x-actor-role": context.actorRole,
    "x-clinic-id": context.clinicId,
  };
}

async function request(path, options = {}, context = DEMO_CONTEXT) {
  const response = await fetch(path, {
    ...options,
    headers: {
      ...authHeaders(context),
      ...(options.body ? { "content-type": "application/json" } : {}),
      ...options.headers,
    },
  });
  if (!response.ok) {
    let message = "Unable to load the patient record";
    try {
      const payload = await response.json();
      message = payload.detail || message;
    } catch {
      // Keep the safe generic message when the server response is not JSON.
    }
    throw new ApiError(message, response.status);
  }
  return response.json();
}

export function addComment(content, assignedTo, parentId = null, context = DEMO_CONTEXT) {
  return request(`/api/patients/${context.patientId}/comments`, {
    method: "POST",
    body: JSON.stringify({ content, assigned_to: assignedTo || null, parent_id: parentId }),
  }, context);
}

export function setCommentResolved(commentId, resolved, context = DEMO_CONTEXT) {
  return request(`/api/patients/${context.patientId}/comments/${commentId}`, {
    method: "PATCH",
    body: JSON.stringify({ resolved }),
  }, context);
}

export function updateHighlight(highlightId, changes, context = DEMO_CONTEXT) {
  return request(`/api/patients/${context.patientId}/highlights/${highlightId}`, {
    method: "PATCH",
    body: JSON.stringify(changes),
  }, context);
}

export function addTimelineEntry(title, content, context = DEMO_CONTEXT) {
  return request(`/api/patients/${context.patientId}/entries`, {
    method: "POST",
    body: JSON.stringify({ title, content }),
  }, context);
}

export function createHighlight(payload, context = DEMO_CONTEXT) {
  return request(`/api/patients/${context.patientId}/highlights`, {
    method: "POST",
    body: JSON.stringify(payload),
  }, context);
}

export function getAuditEvents(context = DEMO_CONTEXT) {
  return request(`/api/patients/${context.patientId}/audit`, {}, context);
}

export function updateSection(section, content, expectedVersion, context = DEMO_CONTEXT) {
  return request(`/api/patients/${context.patientId}/sections/${section}`, {
    method: "PUT",
    body: JSON.stringify({ content, expected_version: expectedVersion }),
  }, context);
}

export function getSectionRevisions(section, context = DEMO_CONTEXT) {
  return request(`/api/patients/${context.patientId}/sections/${section}/revisions`, {}, context);
}

export function revertSection(section, targetVersion, context = DEMO_CONTEXT) {
  return request(`/api/patients/${context.patientId}/sections/${section}/revert`, {
    method: "POST",
    body: JSON.stringify({ target_version: targetVersion }),
  }, context);
}
