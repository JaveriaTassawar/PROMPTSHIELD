import { useEffect, useState } from 'react'
import { mockFetchProfile } from '../mocks/profile.js'

// The current user's profile for the Profile page (Task 92). Today it reads the
// local mock; when GET /api/profile is wired to this page, only the fetch call
// and toProfile() change — components keep the same shape.
//   status: 'loading' | 'unavailable' (API not connected) | 'success' | 'error'

// A User-model record → display fields. The role string is kept exactly as sent.
function toProfile(raw) {
  const joined = raw.created_at ? new Date(raw.created_at) : null

  return {
    sample: raw.sample === true,
    name: typeof raw.user_name === 'string' && raw.user_name.trim() !== '' ? raw.user_name.trim() : null,
    email: typeof raw.email === 'string' ? raw.email : null,
    role: typeof raw.role === 'string' && raw.role !== '' ? raw.role : null,
    joined: joined && !Number.isNaN(joined.getTime()) ? joined : null,
  }
}

export function useProfile() {
  const [state, setState] = useState({ status: 'loading', profile: null })

  useEffect(() => {
    let active = true
    mockFetchProfile()
      .then((raw) => {
        if (active) setState(raw ? { status: 'success', profile: toProfile(raw) } : { status: 'unavailable', profile: null })
      })
      .catch(() => {
        if (active) setState({ status: 'error', profile: null })
      })
    return () => {
      active = false
    }
  }, [])

  return state
}
