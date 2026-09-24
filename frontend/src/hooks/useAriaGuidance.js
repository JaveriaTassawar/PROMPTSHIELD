import { useMemo } from 'react'
import { getGeneralGuidance } from '../config/ariaGuidance.js'

// Guidance for Aria's panel. Today it is always the fixed general guidance for
// the result's classification and sub-type. Task 82 replaces or supplements it
// with POST /api/avatar-guide here — the panel only receives the guidance
// object, so it does not change.
export function useAriaGuidance(result) {
  return useMemo(() => (result ? getGeneralGuidance(result) : null), [result])
}
