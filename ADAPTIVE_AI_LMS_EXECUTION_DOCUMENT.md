# Adaptive AI LMS Generator - Execution Document

## Purpose
This document captures the current understanding of the project direction and the exact implementation sequence to follow next.

## Current Direction (As Understood)
- The project should follow a **data-first** approach.
- AI should help **curate/transform structured information**, not bypass schema rules.
- Core role model includes:
  - `admin`
  - `manager`
  - `employee`
- Login model should support `username` and `password`.
- LMS data should include foundational modules such as:
  - lessons
  - assignments
  - sessions
  - additional module entities as needed

## High-Level Flow
1. Input is gathered from the frontend.
2. AI/LLM stage understands and curates the input.
3. Database schema and structure are generated/validated.
4. Any modified data remains strictly schema-compliant.
5. Frontend is updated to reflect the finalized backend schema.

## Implementation Sequence (What to Do Next)

### 1) Freeze the Canonical Schema
- Define one authoritative schema for:
  - users
  - roles/permissions
  - modules
  - lessons
  - assignments
  - sessions
- Mark required vs optional fields clearly.
- Finalize consistent naming (no duplicate concepts with different names).

### 2) Lock Authentication + Role Mapping
- Ensure `admin`, `manager`, and `employee` login flows are explicit.
- Map each role to allowed features/actions.
- Confirm credential fields and validation rules.

### 3) Make AI Output Schema-Safe
- AI output should be transformed to a strict internal format.
- Add validation checks so malformed AI output is rejected/fixed before save.
- Ensure transformed output never breaks database constraints.

### 4) Align Backend APIs with Schema
- Every API request/response should match canonical schema contracts.
- Remove ad-hoc fields that are not in schema.
- Add backend-side validation for all create/update endpoints.

### 5) Align Frontend with Final Contracts
- Forms should collect only schema-approved fields.
- UI data models should match backend response shape.
- Role-based screens/actions should be enforced in UX logic.

### 6) Validation and Stability Pass
- Test role-based login for all roles.
- Test create/read/update flows for modules, lessons, assignments, sessions.
- Verify AI-generated/curated data can be stored and displayed safely.
- Confirm no frontend/backend field mismatch remains.

## Suggested Deliverables
- `schema` document (tables/entities + relationships)
- role-permission matrix
- API contract reference
- AI transformation/validation rule sheet
- frontend field-to-schema mapping checklist

## Definition of Done
- One canonical schema is used across AI, backend, and frontend.
- Role-based access behaves correctly for `admin`, `manager`, `employee`.
- AI-curated data is always validated before persistence.
- No contract mismatch exists between frontend and backend.
- Core LMS flows are tested and reproducible.

## Notes
This document is intended as the execution baseline before starting the next coding phase.
