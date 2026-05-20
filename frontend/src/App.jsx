import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Signup from './pages/Signup'
import ManufacturerDashboard from './pages/ManufacturerDashboard'
import CreateBatch from './pages/CreateBatch'
import DispatchShipment from './pages/DispatchShipment'
import SupplierDashboard from './pages/SupplierDashboard'
import HospitalDashboard from './pages/HospitalDashboard'
import ApprovalLogPage from './pages/ApprovalLogPage'
import PublicShipmentPage from './pages/PublicShipmentPage'
import CrisisDashboard from './pages/CrisisDashboard'

function HomeRedirect() {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (user.role === 'manufacturer') return <Navigate to="/manufacturer" replace />
  if (user.role === 'supplier') return <Navigate to="/supplier" replace />
  if (user.role === 'consumer') return <Navigate to="/hospital" replace />
  return <Navigate to="/login" replace />
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route path="/shared/shipment/:id" element={<PublicShipmentPage />} />
          <Route path="/" element={<HomeRedirect />} />

          {/* Shared protected routes — all roles */}
          <Route
            path="/approval-log"
            element={
              <ProtectedRoute>
                <ApprovalLogPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/crisis"
            element={
              <ProtectedRoute>
                <CrisisDashboard />
              </ProtectedRoute>
            }
          />
          {/* Alias for /map → Crisis dashboard (master prompt spec) */}
          <Route
            path="/map"
            element={
              <ProtectedRoute>
                <CrisisDashboard />
              </ProtectedRoute>
            }
          />

          {/* Manufacturer routes */}
          <Route
            path="/manufacturer"
            element={
              <ProtectedRoute role="manufacturer">
                <ManufacturerDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/manufacturer/batch/create"
            element={
              <ProtectedRoute role="manufacturer">
                <CreateBatch />
              </ProtectedRoute>
            }
          />
          <Route
            path="/manufacturer/dispatch"
            element={
              <ProtectedRoute role="manufacturer">
                <DispatchShipment />
              </ProtectedRoute>
            }
          />

          {/* Supplier routes */}
          <Route
            path="/supplier"
            element={
              <ProtectedRoute role="supplier">
                <SupplierDashboard />
              </ProtectedRoute>
            }
          />

          {/* Hospital / Consumer routes */}
          <Route
            path="/hospital"
            element={
              <ProtectedRoute role="consumer">
                <HospitalDashboard />
              </ProtectedRoute>
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
