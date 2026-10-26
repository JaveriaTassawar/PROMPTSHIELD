// Mock stand-in for GET /api/admin/users until Task 91 wires the real endpoint
// (Backend Task 65). No accounts exist and no permissions are checked.
//
// Which response comes back:
//   /admin                  → null: the admin users API is not connected
//   /admin?mock=preview     → SAMPLE_USERS (synthetic, for visual checks only)
//   /admin?mock=empty       → no user accounts
//   /admin?mock=forbidden   → a 403 error — previews the future access-denied
//                             state only; the frontend checks no roles today
//   /admin?mock=error       → the request fails
//
// Response shape is PROVISIONAL: Backend Task 65 doesn't define one. Records use
// the User model fields (Backend Task 41) minus the password hash. The hook's
// toUser() is the only place that reads this shape.
const MOCK_DELAY_MS = 600

// SYNTHETIC SAMPLE — made-up accounts. Roles use only values that appear in
// both the SDS and Backend Task 55 role lists (the rest is still unresolved).
const SAMPLE_USERS = [
  { user_id: 1, user_name: 'Sample User 1', email: 'sample.user1@example.com', role: 'student', created_at: '2026-09-01T09:15:00Z' },
  { user_id: 2, user_name: 'Sample User 2', email: 'sample.user2@example.com', role: 'developer', created_at: '2026-09-03T14:40:00Z' },
  { user_id: 3, user_name: 'Sample User 3', email: 'sample.user3@example.com', role: 'researcher', created_at: '2026-09-08T11:05:00Z' },
  { user_id: 4, user_name: 'Sample User 4', email: 'sample.user4@example.com', role: 'student', created_at: '2026-09-12T16:20:00Z' },
  { user_id: 5, user_name: 'Sample User 5', email: 'sample.user5@example.com', role: 'developer', created_at: '2026-09-17T08:50:00Z' },
  { user_id: 6, user_name: 'Sample User 6', email: 'sample.user6@example.com', role: 'student', created_at: '2026-09-21T13:30:00Z' },
]

function httpError(status, message) {
  const error = new Error(message)
  error.status = status
  return error
}

export function mockFetchAdminUsers() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const flag = new URLSearchParams(window.location.search).get('mock')
      if (flag === 'forbidden') reject(httpError(403, 'Forbidden'))
      else if (flag === 'error') reject(httpError(500, 'Admin users request failed.'))
      else if (flag === 'preview') resolve({ sample: true, users: SAMPLE_USERS })
      else if (flag === 'empty') resolve({ users: [] })
      else resolve(null)
    }, MOCK_DELAY_MS)
  })
}
