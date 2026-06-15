/* eslint-disable no-unused-vars */
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/auth-context";
import {
  BarChart3,
  Mail,
  Lock,
  Eye,
  EyeOff,
  Clock,
  XCircle,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { Toaster } from "sonner";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [accountStatus, setAccountStatus] = useState(null);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const result = await login(email, password);
      if (result.success) {
        if (result.status === "pending") {
          setAccountStatus("pending");
          setShowStatusModal(true);
        } else if (result.status === "rejected") {
          setAccountStatus("rejected");
          setShowStatusModal(true);
        } else if (result.status === "approved") {
          toast.success("Login successful!");
          navigate("/dashboard");
        }
      } else {
        toast.error("Invalid credentials. Please try again.");
      }
    } catch (error) {
      console.error("Login error:", error);
      toast.error(error.message || "An error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const closeModal = () => {
    setShowStatusModal(false);
    setAccountStatus(null);
    setEmail("");
    setPassword("");
  };

  return (
    <div className="min-h-screen bg-[#f5f3ef] flex items-center justify-center p-4">
      <Toaster position="top-center" richColors />

      <div className="w-full max-w-3xl flex rounded-2xl overflow-hidden shadow-2xl">
        {/* ── Left Panel ── */}
        <div className="hidden md:flex w-[44%] bg-[#1a1a2e] flex-col justify-between p-10 relative overflow-hidden">
          {/* Decorative circles */}
          <div className="absolute -top-14 -right-14 w-64 h-64 rounded-full bg-indigo-500/20 pointer-events-none" />
          <div className="absolute -bottom-10 -left-10 w-44 h-44 rounded-full bg-indigo-500/10 pointer-events-none" />

          {/* Brand */}
          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-8">
              <div className="w-9 h-9 bg-indigo-500 rounded-xl flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-white" />
              </div>
              <span className="text-white font-semibold text-sm tracking-tight">
                WorkForce Analytics
              </span>
            </div>

            <p className="text-white text-2xl font-light leading-snug mb-4 italic">
              Data-driven decisions for your team.
            </p>
            <p className="text-white/50 text-xs leading-relaxed">
              Real-time workforce insights, attendance tracking, and performance
              metrics in one unified platform.
            </p>
          </div>

          {/* Stat chips */}
          <div className="relative z-10 flex flex-col gap-3">
            {[
              { dot: "bg-indigo-400", label: "Active employees tracked", value: "1,240" },
              { dot: "bg-emerald-400", label: "Reports generated today", value: "84" },
              { dot: "bg-amber-400", label: "Uptime this month", value: "99.9%" },
            ].map((s) => (
              <div
                key={s.label}
                className="flex items-center gap-3 bg-white/5 border border-white/10 rounded-xl px-4 py-3"
              >
                <span className={`w-2 h-2 rounded-full flex-shrink-0 ${s.dot}`} />
                <span className="text-white/50 text-xs flex-1">{s.label}</span>
                <span className="text-white text-sm font-medium">{s.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* ── Right Panel (Form) ── */}
        <div className="flex-1 bg-white flex flex-col justify-center px-8 py-10">
          {/* Mobile brand */}
          <div className="flex items-center gap-2 mb-6 md:hidden">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-white" />
            </div>
            <span className="text-slate-900 font-semibold text-sm">WorkForce Analytics</span>
          </div>

          <div className="mb-7">
            <h2 className="text-2xl font-semibold text-slate-900 tracking-tight mb-1">
              Welcome back
            </h2>
            <p className="text-slate-400 text-sm">Sign in to access your dashboard</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email */}
            <div>
              <label className="block text-[11px] font-medium text-slate-500 uppercase tracking-wider mb-2">
                Work Email
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="j.smith@company.com"
                  required
                  className="w-full pl-10 pr-4 h-11 border border-slate-200 bg-slate-50 rounded-xl text-sm text-slate-900 placeholder:text-slate-300 outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 focus:bg-white transition-all"
                />
              </div>
              <p className="text-[11px] text-slate-400 mt-1.5">Use your work email address</p>
            </div>

            {/* Password */}
            <div>
              <label className="block text-[11px] font-medium text-slate-500 uppercase tracking-wider mb-2">
                Password
              </label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  className="w-full pl-10 pr-10 h-11 border border-slate-200 bg-slate-50 rounded-xl text-sm text-slate-900 placeholder:text-slate-300 outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 focus:bg-white transition-all"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Forgot */}
            <div className="flex justify-end">
              <Link
                to="/forgot-password"
                className="text-xs text-indigo-600 hover:text-indigo-700 font-medium"
              >
                Forgot password?
              </Link>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full h-11 bg-[#1a1a2e] hover:bg-[#2d2d4e] disabled:bg-slate-400 text-white rounded-xl text-sm font-medium transition-colors flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  Signing in...
                </>
              ) : (
                "Sign in"
              )}
            </button>
          </form>

          <div className="text-center mt-6">
            <Link to="/" className="text-xs text-slate-400 hover:text-slate-600 transition-colors">
              ← Back to Home
            </Link>
          </div>
        </div>
      </div>

      {/* ── Status Modal ── */}
      {showStatusModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl max-w-sm w-full p-8 relative">
            <button
              onClick={closeModal}
              className="absolute top-4 right-4 text-slate-300 hover:text-slate-500 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            {accountStatus === "pending" ? (
              <div className="text-center">
                <div className="w-14 h-14 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Clock className="w-7 h-7 text-amber-500" />
                </div>
                <h2 className="text-lg font-semibold text-slate-900 mb-2">
                  Account pending approval
                </h2>
                <p className="text-sm text-slate-500 mb-5 leading-relaxed">
                  Your account is currently under review. Please wait for
                  administrator approval to access the system.
                </p>
                <div className="bg-amber-50 border border-amber-100 rounded-xl p-4 mb-5 text-left">
                  <p className="text-xs text-amber-800 leading-relaxed">
                    <strong>What's next?</strong>
                    <br />
                    You'll receive an email once your account has been approved
                    by the administrator.
                  </p>
                </div>
                <button
                  onClick={closeModal}
                  className="w-full h-10 bg-amber-500 hover:bg-amber-600 text-white rounded-xl text-sm font-medium transition-colors"
                >
                  Understood
                </button>
              </div>
            ) : (
              <div className="text-center">
                <div className="w-14 h-14 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <XCircle className="w-7 h-7 text-red-500" />
                </div>
                <h2 className="text-lg font-semibold text-slate-900 mb-2">
                  Account rejected
                </h2>
                <p className="text-sm text-slate-500 mb-5 leading-relaxed">
                  Your account request has been rejected. Please contact your
                  manager or administrator for more information.
                </p>
                <div className="bg-red-50 border border-red-100 rounded-xl p-4 mb-5 text-left">
                  <p className="text-xs text-red-800 leading-relaxed">
                    <strong>Need help?</strong>
                    <br />
                    Contact your manager or HR department to discuss your
                    account status and next steps.
                  </p>
                </div>
                <button
                  onClick={closeModal}
                  className="w-full h-10 bg-red-500 hover:bg-red-600 text-white rounded-xl text-sm font-medium transition-colors"
                >
                  Close
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}