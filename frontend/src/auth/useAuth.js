// Access the auth state (frontend Task 72).
//
// Separate from AuthContext.jsx because a module exporting both a
// component and a plain function breaks Vite's Fast Refresh -- editing
// the provider would do a full reload and drop the session mid-work.

import { useContext } from 'react'

import { AuthContext } from './context.js'

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === null) {
    throw new Error('useAuth must be used inside <AuthProvider>')
  }
  return context
}
