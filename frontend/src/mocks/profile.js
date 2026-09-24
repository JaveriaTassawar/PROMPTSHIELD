// Mock stand-in for GET /api/profile (Backend Task 54). No frontend task wires
// the real endpoint to this page yet, and the frontend cannot tell whether
// anyone is signed in.
//
// Which response comes back:
//   /profile                → null: authentication/profile API not connected
//   /profile?mock=preview   → SAMPLE_PROFILE (synthetic, for visual checks only)
//   /profile?mock=error     → the request fails
//
// Response shape is PROVISIONAL: Task 54 doesn't define one. The record uses
// the User model fields (Backend Task 41) minus the password hash. The hook's
// toProfile() is the only place that reads this shape.
const MOCK_DELAY_MS = 600

// SYNTHETIC SAMPLE — not a real account.
const SAMPLE_PROFILE = {
  sample: true,
  user_id: 1,
  user_name: 'Sample User',
  email: 'sample.user@example.com',
  role: 'student',
  created_at: '2026-09-01T09:15:00Z',
}

export function mockFetchProfile() {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const flag = new URLSearchParams(window.location.search).get('mock')
      if (flag === 'error') reject(new Error('Profile request failed.'))
      else if (flag === 'preview') resolve(SAMPLE_PROFILE)
      else resolve(null)
    }, MOCK_DELAY_MS)
  })
}
