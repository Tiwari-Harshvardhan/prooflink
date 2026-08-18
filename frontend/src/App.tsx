import { Routes, Route } from 'react-router-dom'
import Layout from '@/components/Layout'
import Home from '@/pages/Home'
import Verify from '@/pages/Verify'
import VerifyResult from '@/pages/VerifyResult'
import InstitutionDashboard from '@/pages/InstitutionDashboard'
import CreateProofLink from '@/pages/CreateProofLink'
import HowItWorks from '@/pages/HowItWorks'

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/verify" element={<Verify />} />
        <Route path="/verify/result/:proofId" element={<VerifyResult />} />
        <Route path="/institution" element={<InstitutionDashboard />} />
        <Route path="/institution/create" element={<CreateProofLink />} />
        <Route path="/how-it-works" element={<HowItWorks />} />
      </Routes>
    </Layout>
  )
}
