// The auth context object (frontend Task 72).
//
// On its own because Vite's Fast Refresh only works when a module
// exports components alone -- a file exporting both <AuthProvider> and
// this object would force a full reload on every edit, dropping the
// session mid-work.

import { createContext } from 'react'

export const AuthContext = createContext(null)
