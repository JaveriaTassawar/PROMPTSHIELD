// Mock stand-ins for the auth endpoints until Tasks 71–72 wire the real ones.
// No credentials are checked and nothing is saved. Error states can be shown
// with a URL flag:
//   /login?mock=fail      → generic auth error (Backend Task 53)
//   /register?mock=exists → duplicate email (Backend Task 51, TC-02)
const MOCK_DELAY_MS = 800

function mockRequest(failFlag, errorMessage) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const shouldFail = new URLSearchParams(window.location.search).get('mock') === failFlag
      if (shouldFail) {
        reject(new Error(errorMessage))
      } else {
        resolve({ mock: true })
      }
    }, MOCK_DELAY_MS)
  })
}

// Stands in for POST /api/login (Task 72).
export function mockLogin() {
  return mockRequest('fail', 'Invalid email or password.')
}

// Stands in for POST /api/register (Task 71).
export function mockRegister() {
  return mockRequest('exists', 'Email already exists.')
}
