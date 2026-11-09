// Authentication state (frontend Tasks 72 and 73).
//
// Holds the current user and token, and is the only place that writes
// them to storage.
//
// FOUR DECISIONS:
//
// 1. A STORED TOKEN IS VERIFIED AGAINST THE SERVER BEFORE IT IS TRUSTED.
//
//    This is Task 73's actual requirement, and the reason this file is
//    more than a useState. A token in localStorage proves nothing: it
//    may have expired, or the account may have been deactivated since
//    it was issued — the backend checks `is_active` on every request
//    (backend Task 54), so a disabled user's token stops working
//    immediately.
//
//    Treating a stored token as proof of login would show the dashboard
//    to someone whose access was revoked, then fail every request on it.
//
// 2. `status` HAS THREE VALUES, NOT A BOOLEAN.
//
//    'checking' | 'authenticated' | 'anonymous'. With a boolean, the
//    first render after a refresh looks identical to logged-out, so the
//    route guard would bounce an authenticated user to the login page
//    before the profile check came back. The guard waits on 'checking'.
//
// 3. THE TOKEN IS IN localStorage, AND THAT IS A TRADE-OFF WORTH NAMING.
//
//    Task 72 specifies it. It survives a refresh, which a memory-only
//    token does not — but any script running on the page can read it,
//    so an XSS bug becomes a stolen session. httpOnly cookies avoid
//    that, at the cost of backend changes and CSRF handling.
//
//    Documented rather than silently chosen, since this project is
//    about security.
//
// 4. LOGOUT CLEARS STORAGE FIRST, STATE SECOND.
//
//    If a render triggered by the state change throws, the token is
//    already gone. The other order can leave a cleared UI with a live
//    token still on disk.

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { fetchProfile, login as loginRequest } from '../api/auth.js'
import { AuthContext } from './context.js'
import { setAccessToken, setUnauthorizedHandler } from '../api/client.js'

const STORAGE_KEY = 'promptshield.token'

function readStoredToken() {
  try {
    return window.localStorage.getItem(STORAGE_KEY)
  } catch {
    // Private browsing, or storage disabled. Not an error — the user
    // simply logs in again each session.
    return null
  }
}

function writeStoredToken(token) {
  try {
    if (token) window.localStorage.setItem(STORAGE_KEY, token)
    else window.localStorage.removeItem(STORAGE_KEY)
  } catch {
    // Same as above: a session that cannot persist still works.
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)

  // Computed during the first render rather than in an effect: with no
  // stored token there is nothing to verify, so starting at 'checking'
  // and immediately setting 'anonymous' would render a pointless
  // "checking your session" frame on every visit by a logged-out user.
  const [status, setStatus] = useState(() =>
    readStoredToken() ? 'checking' : 'anonymous',
  )

  // Avoids a setState on an unmounted provider if the profile request
  // resolves after a fast navigation away.
  const mounted = useRef(true)
  useEffect(() => () => { mounted.current = false }, [])

  const clearSession = useCallback(() => {
    writeStoredToken(null)   // storage first — see decision 4
    setAccessToken(null)
    if (mounted.current) {
      setUser(null)
      setStatus('anonymous')
    }
  }, [])

  // An expired or revoked token surfaces as a 401 from any request, not
  // just the profile check — so the client notifies us and we drop the
  // session wherever it happened.
  useEffect(() => {
    setUnauthorizedHandler(clearSession)
    return () => setUnauthorizedHandler(null)
  }, [clearSession])

  // Startup: verify a stored token rather than assuming it — decision 1.
  useEffect(() => {
    const stored = readStoredToken()

    // Nothing to verify -- `status` already started as 'anonymous'.
    if (!stored) return

    setAccessToken(stored)

    fetchProfile()
      .then((profile) => {
        if (!mounted.current) return
        setUser(profile)
        setStatus('authenticated')
      })
      .catch(() => {
        // Expired, revoked, deactivated, or the backend is down. All
        // mean "do not show protected pages".
        clearSession()
      })
  }, [clearSession])

  const login = useCallback(async ({ email, password }) => {
    const data = await loginRequest({ email, password })

    setAccessToken(data.access_token)
    writeStoredToken(data.access_token)
    setUser(data.user)
    setStatus('authenticated')

    return data.user
  }, [])

  const logout = useCallback(() => {
    clearSession()
  }, [clearSession])

  const value = useMemo(
    () => ({
      user,
      status,
      isAuthenticated: status === 'authenticated',
      isChecking: status === 'checking',
      login,
      logout,
    }),
    [user, status, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
