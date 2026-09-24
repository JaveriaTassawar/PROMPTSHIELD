import { useEffect, useState } from 'react'
import { mockFetchAdminUsers } from '../mocks/admin.js'

// User records for the Admin panel (Task 90). Today it reads the local mock;
// Task 91 swaps mockFetchAdminUsers() for GET /api/admin/users and adjusts
// toUser() to the real response — components keep the same shape.
//   status: 'loading' | 'unavailable' (API not connected) | 'success'
//         | 'forbidden' (403) | 'error'

// One User-model record → display fields. The role string is kept exactly as
// sent; records without an id are dropped rather than guessed.
function toUser(raw) {
  if (raw?.user_id == null) return null
  const joined = raw.created_at ? new Date(raw.created_at) : null

  return {
    id: raw.user_id,
    name: typeof raw.user_name === 'string' ? raw.user_name : null,
    email: typeof raw.email === 'string' ? raw.email : null,
    role: typeof raw.role === 'string' && raw.role !== '' ? raw.role : null,
    joined: joined && !Number.isNaN(joined.getTime()) ? joined : null,
  }
}

export function useAdminUsers() {
  const [state, setState] = useState({ status: 'loading', users: [], sample: false })

  useEffect(() => {
    let active = true
    mockFetchAdminUsers()
      .then((raw) => {
        if (!active) return
        if (!raw) setState({ status: 'unavailable', users: [], sample: false })
        else setState({ status: 'success', users: (raw.users ?? []).map(toUser).filter(Boolean), sample: raw.sample === true })
      })
      .catch((error) => {
        if (active) setState({ status: error.status === 403 ? 'forbidden' : 'error', users: [], sample: false })
      })
    return () => {
      active = false
    }
  }, [])

  return state
}
