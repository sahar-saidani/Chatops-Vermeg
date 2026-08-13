import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"
import AppLayout from "./components/AppLayout"
import LoginPage from "./components/LoginPage"
import ProtectedRoute from "./components/ProtectedRoute"
import AuthProvider from "./context/AuthContext"
import CredentialSetupPage from "./pages/ActivateAccountPage"
import ForgotPasswordPage from "./pages/ForgotPasswordPage"
import NotImplementedPage from "./pages/NotImplementedPage"
import ChatPage from "./pages/ChatPage"
import DashboardPage from "./pages/DashboardPage"
import UserManagement from "./pages/UserManagement"
import RolesPage from "./pages/RolesPage"
import PermissionsPage from "./pages/PermissionsPage"
import TenantsPage from "./pages/TenantsPage"
import EnvironmentsPage from "./pages/EnvironmentsPage"
import AgentPage from "./pages/AgentPage"
import LogsPage from "./pages/LogsPage"
import HistoryPage from "./pages/HistoryPage"
import SettingsPage from "./pages/SettingsPage"
import { PERMISSIONS } from "./types"

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public: the three entry points AuthenticationMailServiceImpl links to. */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/activate" element={<CredentialSetupPage mode="activate" />} />
          <Route path="/reset-password" element={<CredentialSetupPage mode="reset" />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />

          <Route
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          >
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/chat" element={<ChatPage />} />

            <Route
              path="/users"
              element={
                <ProtectedRoute anyPermission={[PERMISSIONS.userRead]}>
                  <UserManagement />
                </ProtectedRoute>
              }
            />
            <Route
              path="/roles"
              element={
                <ProtectedRoute anyPermission={[PERMISSIONS.roleManage]}>
                  <RolesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/permissions"
              element={
                <ProtectedRoute anyPermission={[PERMISSIONS.permissionManage]}>
                  <PermissionsPage />
                </ProtectedRoute>
              }
            />
            <Route path="/tenants" element={<TenantsPage />} />
            <Route
              path="/environments"
              element={
                <ProtectedRoute anyPermission={[PERMISSIONS.environmentRead]}>
                  <EnvironmentsPage />
                </ProtectedRoute>
              }
            />

            <Route path="/git" element={<AgentPage agentKey="git" />} />
            <Route path="/jenkins" element={<AgentPage agentKey="jenkins" />} />
            <Route path="/installation" element={<AgentPage agentKey="installation" />} />
            {/* Logs get a dedicated view: the generic agent page renders raw
                JSON, which does not scale to thousands of entries. */}
            <Route path="/logs" element={<LogsPage />} />
            <Route path="/infrastructure" element={<AgentPage agentKey="infrastructure" />} />

            <Route path="/history" element={<HistoryPage />} />
            <Route path="/settings" element={<SettingsPage />} />

            <Route
              path="*"
              element={
                <NotImplementedPage
                  title="Page not found"
                  reason="This address does not match any section of the application."
                />
              }
            />
          </Route>

          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
