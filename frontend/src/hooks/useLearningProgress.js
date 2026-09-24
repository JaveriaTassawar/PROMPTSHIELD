import { useCallback, useEffect, useState } from 'react'

// Learning progress for the Learning Hub (Task 87) — local preview only.
// Completion is recorded only when the user marks a module complete, and is
// stored in this browser's localStorage; nothing is synced to an account.
// No backend API for LearningProgress (Backend Task 49 model) is planned yet —
// when one exists, only this hook changes.
const STORAGE_KEY = 'promptshield.learningProgress.v1'

function readCompleted(validIds) {
  try {
    const stored = JSON.parse(window.localStorage.getItem(STORAGE_KEY))
    return Array.isArray(stored) ? stored.filter((id) => validIds.includes(id)) : []
  } catch {
    return []
  }
}

export function useLearningProgress(moduleIds) {
  const [completedIds, setCompletedIds] = useState(() => readCompleted(moduleIds))

  useEffect(() => {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(completedIds))
    } catch {
      // Storage unavailable (e.g. private mode): progress lasts for this visit only.
    }
  }, [completedIds])

  const toggleComplete = useCallback((id) => {
    setCompletedIds((prev) => (prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]))
  }, [])

  return { completedIds, toggleComplete }
}
