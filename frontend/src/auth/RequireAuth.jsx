// Route guard (frontend Task 73).
//
// Wraps protected routes and sends anonymous visitors to the login page.
//
// TWO DECISIONS:
//
// 1. IT WAITS WHILE THE STORED TOKEN IS BEING VERIFIED.
//
//    On a refresh, AuthContext starts in 'checking' and asks the server
//    whether the stored token is still good. Redirecting during that
//    window would bounce a perfectly authenticated user to the login
//    page every time they pressed F5 — the single most common bug in
//    hand-rolled route guards.
//
// 2. IT REMEMBERS WHERE THE USER WAS GOING.
//
//    `state.from` carries the attempted path, so after logging in they
//    land where they meant to rather than on a generic dashboard.
//    `replace` keeps the guarded URL out of history, so Back does not
//    bounce them between login and a page they cannot see.

import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from './useAuth.js'

export function RequireAuth() {
  const { isAuthenticated, isChecking } = useAuth()
  const location = useLocation()

  if (isChecking) {
    // Deliberately minimal: this is on screen for one request, and a
    // spinner that flashes for 80ms reads as a glitch.
    return (
      <div
        className="flex min-h-[40vh] items-center justify-center text-fg-muted"
        role="status"
        aria-live="polite"
      >
        <span className="text-sm">Checking your session…</span>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}
