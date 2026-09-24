import { Suspense, lazy } from 'react'
import { Routes, Route } from 'react-router-dom'
import AmbientBackground from './components/AmbientBackground.jsx'
import AppLayout from './components/AppLayout.jsx'
import AuthLayout from './components/AuthLayout.jsx'
import PageLoading from './components/PageLoading.jsx'
import AdminPage from './pages/AdminPage.jsx'
import AnalyzerPage from './pages/AnalyzerPage.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import HomePage from './pages/HomePage.jsx'
import LearningHubPage from './pages/LearningHubPage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import NotFoundPage from './pages/NotFoundPage.jsx'
import ProfilePage from './pages/ProfilePage.jsx'
import RegisterPage from './pages/RegisterPage.jsx'
import SimulationLabPage from './pages/SimulationLabPage.jsx'
import SimulationResultsPage from './pages/SimulationResultsPage.jsx'
import SimulationSessionPage from './pages/SimulationSessionPage.jsx'

// Loaded on demand so the charting library (recharts) isn't in the main bundle.
const AnalyticsPage = lazy(() => import('./pages/AnalyticsPage.jsx'))

function App() {
  return (
    <>
      <AmbientBackground />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route element={<AuthLayout />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
        </Route>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/analyzer" element={<AnalyzerPage />} />
          <Route path="/simulation" element={<SimulationLabPage />} />
          <Route path="/simulation/:scenarioId" element={<SimulationSessionPage />} />
          <Route path="/simulation/:scenarioId/results" element={<SimulationResultsPage />} />
          <Route path="/learning" element={<LearningHubPage />} />
          <Route
            path="/analytics"
            element={
              <Suspense fallback={<PageLoading label="Loading analytics…" />}>
                <AnalyticsPage />
              </Suspense>
            }
          />
          <Route path="/profile" element={<ProfilePage />} />
          {/* URL-only (not in the sidebar) until authentication and roles exist — Task 90. */}
          <Route path="/admin" element={<AdminPage />} />
        </Route>
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </>
  )
}

export default App
