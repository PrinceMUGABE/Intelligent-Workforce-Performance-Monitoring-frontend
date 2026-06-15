/* eslint-disable no-unused-vars */
import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router';
import LandingPage from './app/components/landing-page';
import LoginPage from './app/components/login-page';
import ForgotPasswordPage from './app/components/forgot-password-page';
import DashboardLayout from './app/components/dashboard-layout';
import { AuthProvider, useAuth } from './app/context/auth-context';

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }
  
  return <>{children}</>;
}

function AppRoutes() {
  const { isAuthenticated } = useAuth();
  
  return (
    <Routes>
      <Route path="/" element={isAuthenticated ? <Navigate to="/dashboard" /> : <LandingPage />} />
      <Route path="/login" element={isAuthenticated ? <Navigate to="/dashboard" /> : <LoginPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route
        path="/dashboard/*"
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </Router>
  );
}