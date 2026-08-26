export const DEMO_CONTEXT = Object.freeze({
  patientId: "20000000-0000-4000-8000-000000000001",
  actorId: "40000000-0000-4000-8000-000000000001",
  actorRole: "clinician",
  clinicId: "10000000-0000-4000-8000-000000000001",
});

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function getPatientDetail(context = DEMO_CONTEXT) {
  const response = await fetch(`/api/patients/${context.patientId}`, {
    headers: {
      "x-actor-id": context.actorId,
      "x-actor-role": context.actorRole,
      "x-clinic-id": context.clinicId,
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
