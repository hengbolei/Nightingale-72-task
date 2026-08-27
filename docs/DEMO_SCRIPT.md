# Demo Script

Target duration: 3–4 minutes.

1. Open the synthetic clinician view and identify the top action, its risk reason and suggested
   action within ten seconds.
2. Click a Glance card. Show the exact source timeline entry highlighted in context, including the
   AI or human source label and review state.
3. Switch to Staff, add a manual follow-up note, and show that it appears in the Timeline and
   metadata-only Audit Trail.
4. Switch to Clinician, select an exact phrase from the new note or an AI entry, choose “Use
   selected text”, then create and assign a highlight. Show the new Glance item and its provenance.
5. In Care-team comments, enter `@staff please arrange the BP check`, assign it to Staff, submit it,
   then resolve and reopen it.
6. Edit the Care Plan and save a new version. Refresh history, point out actor/time/operation and
   the complete snapshot, then revert to version 1.
7. Use the API documentation or automated test output to show patient filtering, cross-clinic
   rejection and stale-version conflict behavior.
8. Switch to Patient. Show only clinician-published guidance and the patient's public Timeline,
   submit a symptom update, and confirm that internal comments and raw AI notes are absent.
9. Show the PHI gateway tests and state clearly that no external LLM is connected.
10. Close with the benchmark result and the explicit production gaps.

Do not imply that AI-suggested content is clinician-confirmed or that the prototype is a medical
device.
