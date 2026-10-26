// Auth API calls (frontend Tasks 71–73).
//
// Thin wrappers over the three backend endpoints, kept separate from the
// axios instance so a page imports `login` rather than knowing the URL.
//
// FIELD NAMES MATCH THE BACKEND CONTRACT.
//
// The register form posts `name`, which the backend accepts as an alias
// for `user_name` (backend Task 50). The response uses snake_case for
// user fields and camelCase for analysis fields — that split is the
// backend's, documented in backend/TASKS.md, and is not worth
// normalising here where it would just hide the real shape.

import { api } from './client.js'

// POST /api/register → 201, or 409 if the email is taken.
//
// `role` is one of student | developer | researcher | organization.
// `admin` is rejected with 422: the endpoint is unauthenticated, so the
// backend refuses to let a visitor grant themselves that (backend Task
// 50). RegisterPage already omits it from its options.
export async function register({ name, email, password, role }) {
  const { data } = await api.post('/api/register', { name, email, password, role })
  return data
}

// POST /api/login → { access_token, token_type, expires_in_minutes, user }
//
// 401 for both a wrong password and an unknown email, with an identical
// message — the backend does that on purpose so the endpoint cannot be
// used to discover which emails have accounts. Do not try to tell them
// apart in the UI; there is nothing to tell.
export async function login({ email, password }) {
  const { data } = await api.post('/api/login', { email, password })
  return data
}

// GET /api/profile → the authenticated user.
//
// Used by Task 73 to verify a token from localStorage is still good. A
// stored token proves nothing on its own: it may be expired, or the
// account may have been deactivated since.
export async function fetchProfile() {
  const { data } = await api.get('/api/profile')
  return data
}
