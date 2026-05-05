import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import useAuthStore from './store/authStore'
import Layout from './components/Layout/Layout'
import Login from './pages/Auth/Login'
import Dashboard from './pages/Dashboard/Dashboard'
import TopicsList from './pages/Topics/TopicsList'
import TopicDetail from './pages/Topics/TopicDetail'
import ProposeTopic from './pages/Topics/ProposeTopic'
import TopicCatalog from './pages/Topics/TopicCatalog'
import Analytics from './pages/Analytics/Analytics'
import RiskDashboard from './pages/Analytics/RiskDashboard'
import Messages from './pages/Messages/Messages'
import Notifications from './pages/Notifications/Notifications'
import UsersPage from './pages/Users/Users'
import MyStudents from './pages/Supervisor/MyStudents'
import Meetings from './pages/Meetings/Meetings'
import Profile from './pages/Profile/Profile'

function RequireAuth({ children }) {
  const { user, loading } = useAuthStore()
  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full" />
    </div>
  )
  return user ? children : <Navigate to="/login" replace />
}

export default function App() {
  const { init } = useAuthStore()
  useEffect(() => { init() }, [])

  return (
    <BrowserRouter>
      <Toaster position="top-right" />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<RequireAuth><Layout /></RequireAuth>}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard"     element={<Dashboard />} />
          <Route path="topics"          element={<TopicsList />} />
          <Route path="topics/propose"  element={<ProposeTopic />} />
          <Route path="topics/catalog"  element={<TopicCatalog />} />
          <Route path="topics/:id"      element={<TopicDetail />} />
          <Route path="supervisor/students" element={<MyStudents />} />
          <Route path="analytics"     element={<Analytics />} />
          <Route path="risk"          element={<RiskDashboard />} />
          <Route path="messages"      element={<Messages />} />
          <Route path="notifications" element={<Notifications />} />
          <Route path="users"         element={<UsersPage />} />
          <Route path="meetings"      element={<Meetings />} />
          <Route path="profile"       element={<Profile />} />
          <Route path="*"             element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

