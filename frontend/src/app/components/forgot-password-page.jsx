import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { BarChart3, Mail, Lock, Key, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import { Toaster } from 'sonner';
import { useAuth } from '../context/auth-context';

const STEPS = [
  { id: 1, label: 'Enter email', desc: "We'll send a one-time code" },
  { id: 2, label: 'Verify OTP', desc: 'Valid for 30 seconds' },
  { id: 3, label: 'New password', desc: 'Strong password required' },
];

function StepIndicator({ current }) {
  return (
    <div className="flex flex-col gap-0">
      {STEPS.map((s, i) => {
        const done = current > s.id;
        const active = current === s.id;
        return (
          <div key={s.id} className="flex items-start gap-3 py-3 relative">
            {i < STEPS.length - 1 && (
              <div className="absolute left-[15px] top-[38px] w-px h-[calc(100%-10px)] bg-white/10" />
            )}
            <div
              className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-semibold transition-all ${
                done
                  ? 'bg-emerald-500 text-white'
                  : active
                  ? 'bg-indigo-500 text-white'
                  : 'bg-white/[0.08] text-white/30 border border-white/10'
              }`}
            >
              {done ? <CheckCircle className="w-4 h-4" /> : s.id}
            </div>
            <div className="pt-1">
              <div
                className={`text-xs font-medium transition-colors ${
                  done ? 'text-emerald-400' : active ? 'text-white' : 'text-white/30'
                }`}
              >
                {s.label}
              </div>
              <div className="text-[11px] text-white/25 mt-0.5">{s.desc}</div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function FieldLabel({ children }) {
  return (
    <label className="block text-[11px] font-medium text-slate-500 uppercase tracking-wider mb-1.5">
      {children}
    </label>
  );
}

function TextInput({ icon: Icon, ...props }) {
  return (
    <div className="relative">
      <Icon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
      <input
        className="w-full pl-10 pr-4 h-11 border border-slate-200 bg-slate-50 rounded-xl text-sm text-slate-900 placeholder:text-slate-300 outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 focus:bg-white transition-all"
        {...props}
      />
    </div>
  );
}

function PrimaryBtn({ loading, loadingText, children, ...props }) {
  return (
    <button
      className="flex-1 h-11 bg-[#1a1a2e] hover:bg-[#2d2d4e] disabled:bg-slate-300 text-white rounded-xl text-sm font-medium transition-colors flex items-center justify-center gap-2"
      {...props}
    >
      {loading ? (
        <>
          <div className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
          {loadingText}
        </>
      ) : (
        children
      )}
    </button>
  );
}

function SecondaryBtn({ children, ...props }) {
  return (
    <button
      className="flex-1 h-11 bg-slate-100 hover:bg-slate-200 border border-slate-200 text-slate-600 rounded-xl text-sm font-medium transition-colors"
      {...props}
    >
      {children}
    </button>
  );
}

export default function ForgotPasswordPage() {
  const [step, setStep] = useState(1); // 1 = email, 2 = otp, 3 = reset, 4 = success
  const [workEmail, setWorkEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { requestPasswordReset, resetPassword } = useAuth();

  const passwordRules = [
    { id: 'len', label: 'At least 8 characters', test: (p) => p.length >= 8 },
    { id: 'lc', label: 'One lowercase letter', test: (p) => /[a-z]/.test(p) },
    { id: 'uc', label: 'One uppercase letter', test: (p) => /[A-Z]/.test(p) },
    { id: 'num', label: 'One number', test: (p) => /\d/.test(p) },
    { id: 'sym', label: 'One special character (@$!%*?&)', test: (p) => /[@$!%*?&]/.test(p) },
  ];

  const passwordValid = passwordRules.every((r) => r.test(newPassword));
  const passwordsMatch = newPassword === confirmPassword && confirmPassword.length > 0;

  const handleEmailSubmit = async (e) => {
    e.preventDefault();
    if (!workEmail) { toast.error('Please enter your work email'); return; }
    setLoading(true);
    try {
      await requestPasswordReset(workEmail);
      setStep(2);
      toast.success('OTP sent to your registered email!');
    } catch (error) {
      toast.error(error.message || 'Failed to send OTP. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleOtpSubmit = async (e) => {
    e.preventDefault();
    if (!otp || otp.length !== 6) { toast.error('Please enter the 6-digit OTP'); return; }
    setLoading(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/auth/password-reset/verify-otp/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ work_mail_address: workEmail, otp }),
      });
      const data = await response.json();
      if (response.ok) {
        setStep(3);
        toast.success('OTP verified!');
      } else {
        throw new Error(data.error || 'Invalid OTP');
      }
    } catch (error) {
      toast.error(error.message || 'Failed to verify OTP');
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordReset = async (e) => {
    e.preventDefault();
    if (!passwordValid) { toast.error('Password does not meet requirements'); return; }
    if (!passwordsMatch) { toast.error('Passwords do not match'); return; }
    setLoading(true);
    try {
      await resetPassword(workEmail, otp, newPassword, confirmPassword);
      setStep(4);
      toast.success('Password reset successful!');
    } catch (error) {
      toast.error(error.message || 'Failed to reset password. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f5f3ef] flex items-center justify-center p-4">
      <Toaster position="top-center" richColors />

      <div className="w-full max-w-3xl flex rounded-2xl overflow-hidden shadow-2xl">

        {/* ── Left Panel ── */}
        <div className="hidden md:flex w-[42%] bg-[#1a1a2e] flex-col justify-between p-10 relative overflow-hidden">
          <div className="absolute -top-12 -right-12 w-56 h-56 rounded-full bg-indigo-500/15 pointer-events-none" />
          <div className="absolute -bottom-10 -left-10 w-40 h-40 rounded-full bg-indigo-500/08 pointer-events-none" />

          <div className="relative z-10">
            <div className="flex items-center gap-3 mb-8">
              <div className="w-9 h-9 bg-indigo-500 rounded-xl flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-white" />
              </div>
              <span className="text-white font-semibold text-sm tracking-tight">WorkForce Analytics</span>
            </div>
            <p className="text-white text-2xl font-light leading-snug mb-3 italic">
              Secure account recovery, step by step.
            </p>
            <p className="text-white/45 text-xs leading-relaxed">
              Follow three simple steps to verify your identity and set a new password safely.
            </p>
          </div>

          <div className="relative z-10">
            <StepIndicator current={step > 3 ? 3 : step} />
          </div>
        </div>

        {/* ── Right Panel ── */}
        <div className="flex-1 bg-white flex flex-col justify-center px-8 py-10">

          {/* Mobile brand */}
          <div className="flex items-center gap-2 mb-6 md:hidden">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-4 h-4 text-white" />
            </div>
            <span className="text-slate-900 font-semibold text-sm">WorkForce Analytics</span>
          </div>

          {/* ── Step 1: Email ── */}
          {step === 1 && (
            <form onSubmit={handleEmailSubmit}>
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-slate-900 tracking-tight mb-1">Forgot your password?</h2>
                <p className="text-sm text-slate-400 leading-relaxed">Enter your work email and we'll send you an OTP.</p>
              </div>
              <div className="mb-5">
                <FieldLabel>Work email</FieldLabel>
                <TextInput
                  icon={Mail}
                  type="text"
                  value={workEmail}
                  onChange={(e) => setWorkEmail(e.target.value)}
                  placeholder="j.smith@company.com"
                  required
                />
                <p className="text-[11px] text-slate-400 mt-1.5">Use your registered work email address</p>
              </div>
              <div className="flex gap-2">
                <PrimaryBtn type="submit" loading={loading} loadingText="Sending...">
                  Send OTP
                </PrimaryBtn>
              </div>
              <div className="text-center mt-5">
                <Link to="/login" className="text-xs text-indigo-600 hover:text-indigo-700 font-medium">
                  ← Back to login
                </Link>
              </div>
            </form>
          )}

          {/* ── Step 2: OTP ── */}
          {step === 2 && (
            <form onSubmit={handleOtpSubmit}>
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-slate-900 tracking-tight mb-1">Verify OTP</h2>
                <p className="text-sm text-slate-400 leading-relaxed">
                  Enter the 6-digit code sent to{' '}
                  <span className="text-indigo-600 font-medium">{workEmail}</span>
                </p>
                <p className="text-xs text-slate-400 mt-1">OTP expires in 30 seconds</p>
              </div>
              <div className="mb-5">
                <FieldLabel>6-digit OTP</FieldLabel>
                <div className="relative">
                  <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="text"
                    value={otp}
                    onChange={(e) => {
                      const v = e.target.value.replace(/\D/g, '');
                      if (v.length <= 6) setOtp(v);
                    }}
                    className="w-full pl-10 pr-4 h-11 border border-slate-200 bg-slate-50 rounded-xl text-center text-2xl tracking-[10px] font-semibold text-slate-900 outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 focus:bg-white transition-all"
                    placeholder="000000"
                    maxLength={6}
                    required
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <SecondaryBtn type="button" onClick={() => { setStep(1); setOtp(''); }}>Back</SecondaryBtn>
                <PrimaryBtn type="submit" disabled={loading || otp.length !== 6} loading={loading} loadingText="Verifying...">
                  Verify OTP
                </PrimaryBtn>
              </div>
              <div className="text-center mt-4">
                <button
                  type="button"
                  onClick={handleEmailSubmit}
                  className="text-xs text-indigo-600 hover:text-indigo-700 font-medium"
                >
                  Resend OTP
                </button>
              </div>
              <div className="text-center mt-3">
                <Link to="/login" className="text-xs text-indigo-600 hover:text-indigo-700 font-medium">
                  ← Back to login
                </Link>
              </div>
            </form>
          )}

          {/* ── Step 3: New Password ── */}
          {step === 3 && (
            <form onSubmit={handlePasswordReset}>
              <div className="mb-6">
                <h2 className="text-xl font-semibold text-slate-900 tracking-tight mb-1">Create new password</h2>
                <p className="text-sm text-slate-400 leading-relaxed">
                  Set a strong password for{' '}
                  <span className="text-indigo-600 font-medium">{workEmail}</span>
                </p>
              </div>

              <div className="mb-4">
                <FieldLabel>New password</FieldLabel>
                <TextInput
                  icon={Lock}
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Enter new password"
                  required
                />
                <div className="mt-2 space-y-1">
                  {passwordRules.map((r) => (
                    <div
                      key={r.id}
                      className={`flex items-center gap-2 text-xs transition-colors ${
                        r.test(newPassword) ? 'text-emerald-600' : 'text-slate-400'
                      }`}
                    >
                      <div
                        className={`w-1.5 h-1.5 rounded-full transition-colors ${
                          r.test(newPassword) ? 'bg-emerald-500' : 'bg-slate-300'
                        }`}
                      />
                      {r.label}
                    </div>
                  ))}
                </div>
              </div>

              <div className="mb-5">
                <FieldLabel>Confirm password</FieldLabel>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className={`w-full pl-10 pr-4 h-11 border rounded-xl text-sm text-slate-900 placeholder:text-slate-300 bg-slate-50 outline-none focus:bg-white transition-all ${
                      confirmPassword && !passwordsMatch
                        ? 'border-red-300 focus:ring-2 focus:ring-red-400'
                        : 'border-slate-200 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500'
                    }`}
                    placeholder="Confirm new password"
                    required
                  />
                </div>
                {confirmPassword && !passwordsMatch && (
                  <p className="text-xs text-red-500 mt-1">Passwords do not match</p>
                )}
              </div>

              <div className="flex gap-2">
                <SecondaryBtn type="button" onClick={() => setStep(2)}>Back</SecondaryBtn>
                <PrimaryBtn
                  type="submit"
                  disabled={loading || !passwordValid || !passwordsMatch}
                  loading={loading}
                  loadingText="Resetting..."
                >
                  Reset password
                </PrimaryBtn>
              </div>
              <div className="text-center mt-5">
                <Link to="/login" className="text-xs text-indigo-600 hover:text-indigo-700 font-medium">
                  ← Back to login
                </Link>
              </div>
            </form>
          )}

          {/* ── Step 4: Success ── */}
          {step === 4 && (
            <div className="text-center py-4">
              <div className="w-14 h-14 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-7 h-7 text-emerald-600" />
              </div>
              <h2 className="text-xl font-semibold text-slate-900 mb-2 tracking-tight">Password reset!</h2>
              <p className="text-sm text-slate-400 mb-6 leading-relaxed">
                Your password has been updated. You can now log in with your new credentials.
              </p>
              <Link
                to="/login"
                className="inline-block px-7 py-2.5 bg-[#1a1a2e] hover:bg-[#2d2d4e] text-white rounded-xl text-sm font-medium transition-colors"
              >
                Go to login
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}