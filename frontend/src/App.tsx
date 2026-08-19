import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from '@/components/Layout'
import { AuthProvider, useAuth } from '@/context/AuthContext'
import Home from '@/pages/Home'
import Verify from '@/pages/Verify'
import VerifyResult from '@/pages/VerifyResult'
import InstitutionDashboard from '@/pages/InstitutionDashboard'
import CreateProofLink from '@/pages/CreateProofLink'
import HowItWorks from '@/pages/HowItWorks'
import Login from '@/pages/Login'
import Register from '@/pages/Register'
import CitizenVerifyOTP from '@/pages/CitizenVerifyOTP'
import CitizenDashboard from '@/pages/CitizenDashboard'
import DevSmsInbox from '@/pages/DevSmsInbox'

// Protected route wrapper
function ProtectedRoute({ children, role }: { children: React.ReactNode; role?: string }) {
  const { isAuthenticated, user } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (role && user?.role !== role) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<Layout><Home /></Layout>} />
        <Route path="/login" element={<Layout><Login /></Layout>} />
        <Route path="/register" element={<Layout><Register /></Layout>} />
        <Route path="/how-it-works" element={<Layout><HowItWorks /></Layout>} />
        <Route path="/citizen-verify-otp" element={<Layout><CitizenVerifyOTP /></Layout>} />

        {/* Verification routes */}
        <Route path="/verify" element={<Layout><Verify /></Layout>} />
        <Route path="/verify/result/:proofId" element={<Layout><VerifyResult /></Layout>} />

        {/* Citizen routes */}
        <Route
          path="/citizen"
          element={
            <ProtectedRoute role="CITIZEN">
              <Layout>
                <CitizenDashboard />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route path="/citizen/dashboard" element={<ProtectedRoute role="CITIZEN"><Layout><CitizenDashboard /></Layout></ProtectedRoute>} />

        {/* Official routes */}
        <Route
          path="/institution"
          element={
            <ProtectedRoute role="OFFICIAL">
              <Layout>
                <InstitutionDashboard />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route path="/official/dashboard" element={<ProtectedRoute role="OFFICIAL"><Layout><InstitutionDashboard /></Layout></ProtectedRoute>} />
        <Route
          path="/institution/create"
          element={
            <ProtectedRoute role="OFFICIAL">
              <Layout>
                <CreateProofLink />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route path="/official/instructions/create" element={<ProtectedRoute role="OFFICIAL"><Layout><CreateProofLink /></Layout></ProtectedRoute>} />

        {/* Developer tools — backend enforces development-only access */}
        <Route path="/dev/sms-inbox" element={<Layout><DevSmsInbox /></Layout>} />
      </Routes>
    </AuthProvider>
  )
}
