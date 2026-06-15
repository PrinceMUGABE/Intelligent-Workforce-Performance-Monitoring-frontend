import React, { useState } from 'react';
import { useNavigate } from 'react-router';
import { useAuth } from './app/contexts/AuthContext';
import { toast } from 'sonner';
import { Lock, Mail } from 'lucide-react';

export const LoginPage = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await login(email, password);
      toast.success('Login successful!');
      navigate('/dashboard');
    } catch (error) {
      toast.error('Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const demoAccounts = [
    { email: 'admin@company.com', role: 'Admin' },
    { email: 'manager@company.com', role: 'Manager' },
    { email: 'analyst@company.com', role: 'Data Analyst' },
    { email: 'employee@company.com', role: 'Employee' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-sky-50 to-indigo-50 flex items-center justify-center p-4">
      <div className="w-full max-w-5xl grid md:grid-cols-2 gap-8">
        {/* Login Form */}
        <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-xl">
          <div className="mb-8 space-y-2">
            <h2 className="text-3xl font-semibold text-slate-900">Welcome Back</h2>
            <p className="text-slate-600">
              Sign in to access your dashboard
            </p>
          </div>
          <div>
            <form onSubmit={handleLogin} className="space-y-6">
              <div className="space-y-2">
                <label htmlFor="email" className="block text-sm font-medium text-slate-700">Email Address</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-5 w-5 text-slate-400" />
                  <input
                    id="email"
                    type="email"
                    placeholder="you@company.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full pl-10 p-2 border border-slate-300 rounded-md"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label htmlFor="password" className="block text-sm font-medium text-slate-700">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-5 w-5 text-slate-400" />
                  <input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-10 p-2 border border-slate-300 rounded-md"
                    required
                  />
                </div>
              </div>

              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 text-sm text-slate-600">
                  <input type="checkbox" className="rounded border-slate-300" />
                  Remember me
                </label>
                <button
                  type="button"
                  onClick={() => navigate('/forgot-password')}
                  className="text-sky-600 hover:text-sky-700 text-sm"
                >
                  Forgot password?
                </button>
              </div>

              <button
                type="submit"
                className="w-full p-2 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white rounded-md disabled:opacity-50"
                disabled={loading}
              >
                {loading ? 'Signing in...' : 'Sign In'}
              </button>
            </form>
          </div>
        </div>

        {/* Demo Accounts */}
        <div className="bg-white/80 backdrop-blur p-6 rounded-lg border border-slate-200 shadow-xl">
          <div className="mb-8">
            <h2 className="text-2xl font-semibold text-slate-900">Demo Accounts</h2>
            <p className="text-slate-600 mt-1">
              Try different user roles with these demo accounts
            </p>
          </div>
          <div>
            <div className="space-y-3">
              {demoAccounts.map((account) => (
                <button
                  key={account.email}
                  onClick={() => {
                    setEmail(account.email);
                    setPassword('demo123');
                  }}
                  className="w-full p-4 text-left rounded-lg border-2 border-slate-200 hover:border-sky-400 hover:bg-sky-50 transition-colors"
                >
                  <div className="text-sm text-slate-900">{account.email}</div>
                  <div className="text-xs text-slate-500 mt-1">{account.role}</div>
                </button>
              ))}
            </div>
            <div className="mt-6 p-4 bg-sky-50 rounded-lg border border-sky-200">
              <p className="text-sm text-slate-700">
                <strong>Note:</strong> Use any password to login with demo accounts.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};