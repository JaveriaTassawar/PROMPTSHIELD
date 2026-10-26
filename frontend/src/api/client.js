// Axios instance for the PromptShield API (frontend Task 72).
//
// Every request to the backend goes through here, so the token is attached
// in one place rather than remembered at each call site.
//
// THREE DECISIONS:
//
// 1. THE TOKEN IS HELD IN A MODULE VARIABLE, NOT READ FROM localStorage
//    ON EVERY REQUEST.
//
//    localStorage is synchronous and touches disk. More importantly, the
//    in-memory copy is the authority: AuthProvider writes both, and a
//    logout clears both. Reading storage per request would let another
//    tab's stale value leak into this one mid-session.
//
// 2. A 401 CLEARS THE SESSION, BUT DOES NOT REDIRECT FROM HERE.
//
//    This module knows nothing about routing. It notifies whoever
//    registered onUnauthorized, and the auth layer decides what to do.
//    Calling navigate() from an interceptor would couple the HTTP client
//    to React Router and break any non-component caller.
//
// 3. THE BASE URL COMES FROM AN ENV VAR WITH A DEV DEFAULT.
//
//    VITE_API_URL lets a deployed build point somewhere else without a
//    code change. The default matches the backend's own default port and
//    the CORS origins it already allows.

import axios from 'axios'

export const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
  // Long enough for a cold model load on the first /analyze-prompt call,
  // which pays a one-off ~1.2s checkpoint load on the server.
  timeout: 30000,
})

let accessToken = null
let onUnauthorized = null

// Called by AuthProvider on login, logout and startup.
export function setAccessToken(token) {
  accessToken = token ?? null
}

// Lets the auth layer react to an expired or revoked token without this
// module importing React Router. See decision 2.
export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler
}

api.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status

    // 401 means the token is gone, expired or revoked — the backend
    // returns it for all three deliberately, so they cannot be told
    // apart by probing. 403 is different: the caller IS authenticated
    // but lacks the role, or the account was deactivated. Clearing the
    // session on a 403 would log out an admin who clicked one page they
    // happen not to have access to.
    if (status === 401 && onUnauthorized) {
      onUnauthorized()
    }

    return Promise.reject(error)
  },
)

// Turns an axios error into something safe to show a user.
//
// The backend sends { detail: "..." } for its own errors and a Pydantic
// array for 422s. Rendering the raw object would print "[object Object]"
// into the UI, and rendering a stack trace would leak internals.
export function errorMessage(error, fallback = 'Something went wrong. Please try again.') {
  const detail = error?.response?.data?.detail

  if (typeof detail === 'string') return detail

  // Pydantic 422: [{ loc: [...], msg: "...", type: "..." }]
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0]
    if (typeof first?.msg === 'string') {
      return first.msg.replace(/^Value error,\s*/, '')
    }
  }

  if (error?.code === 'ECONNABORTED') return 'The server took too long to respond.'
  if (!error?.response) return 'Could not reach the server. Is the backend running?'

  return fallback
}
