import { Link } from 'react-router';
import {
  BarChart3, Users, TrendingUp, Shield, ChevronRight,
  ArrowRight, CheckCircle, Activity, Database, Clock,
  Award, Globe, Zap, Lock, Star, Building2
} from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white font-sans text-slate-900">

      {/* ── Navbar ── */}
      <header className="sticky top-0 z-50 border-b border-slate-200 bg-white/90 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 bg-indigo-600 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold text-slate-900 tracking-tight">
              CodePulse <span className="text-indigo-600">Analytics</span>
            </span>
          </div>
          <nav className="hidden md:flex items-center gap-8">
            {['Features', 'Roles', 'Stats', 'About'].map((item) => (
              <a
                key={item}
                href={`#${item.toLowerCase()}`}
                className="text-sm font-medium text-slate-600 hover:text-indigo-600 transition-colors"
              >
                {item}
              </a>
            ))}
          </nav>
          <Link
            to="/login"
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold rounded-xl transition-colors flex items-center gap-2 shadow-sm"
          >
            Sign In <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </header>

      {/* ── Hero ── */}
      <section className="max-w-7xl mx-auto px-6 pt-20 pb-24">
        <div className="grid lg:grid-cols-2 gap-16 items-center">

          {/* Left copy */}
          <div className="space-y-8">
            {/* Badge */}
            <span className="inline-flex items-center gap-2 px-4 py-1.5 bg-indigo-50 border border-indigo-200 rounded-full text-xs font-semibold text-indigo-700 uppercase tracking-wider">
              <Zap className="w-3.5 h-3.5" /> Intelligent Workforce Platform
            </span>

            <h1 className="text-5xl font-extrabold leading-tight tracking-tight text-slate-900">
              Monitor. Analyse.
              <span className="block text-indigo-600 mt-1">Empower your team.</span>
            </h1>

            <p className="text-lg text-slate-600 leading-relaxed max-w-lg">
              A unified platform for workforce performance monitoring, real-time analytics,
              leave management, and data-driven decision support — built for every role.
            </p>

            {/* Bullet trust signals */}
            <ul className="space-y-2.5">
              {[
                'Role-based access for admins, managers, analysts & employees',
                'Real-time dashboards with live performance metrics',
                'AI-assisted insights and audit trail for compliance',
              ].map((point) => (
                <li key={point} className="flex items-start gap-3 text-sm text-slate-700">
                  <CheckCircle className="w-4 h-4 text-indigo-500 mt-0.5 flex-shrink-0" />
                  {point}
                </li>
              ))}
            </ul>

            {/* CTAs */}
            <div className="flex flex-wrap gap-4 pt-2">
              <Link
                to="/login"
                className="px-7 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl transition-colors flex items-center gap-2 shadow-md shadow-indigo-200"
              >
                Get started free <ChevronRight className="w-4 h-4" />
              </Link>
              <a
                href="#features"
                className="px-7 py-3 border-2 border-slate-200 hover:border-indigo-400 text-slate-700 hover:text-indigo-600 font-semibold rounded-xl transition-colors"
              >
                Explore features
              </a>
            </div>
          </div>

          {/* Right: dashboard preview card */}
          <div className="relative">
            {/* Floating accent cards */}
            <div className="absolute -top-6 -left-6 z-10 bg-white border border-slate-200 rounded-2xl px-4 py-3 shadow-lg flex items-center gap-3">
              <div className="w-9 h-9 bg-green-100 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-medium">Team Performance</p>
                <p className="text-base font-bold text-slate-900">+24% <span className="text-green-600 text-xs font-semibold">↑ this month</span></p>
              </div>
            </div>

            <div className="absolute -bottom-4 -right-4 z-10 bg-white border border-slate-200 rounded-2xl px-4 py-3 shadow-lg flex items-center gap-3">
              <div className="w-9 h-9 bg-purple-100 rounded-lg flex items-center justify-center">
                <Users className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="text-xs text-slate-500 font-medium">Active Users</p>
                <p className="text-base font-bold text-slate-900">10,482</p>
              </div>
            </div>

            {/* Main dashboard mockup */}
            <div className="bg-slate-900 rounded-3xl overflow-hidden shadow-2xl border border-slate-800 p-5">
              {/* Fake browser bar */}
              <div className="flex items-center gap-2 mb-4">
                <span className="w-3 h-3 rounded-full bg-red-500"></span>
                <span className="w-3 h-3 rounded-full bg-yellow-500"></span>
                <span className="w-3 h-3 rounded-full bg-green-500"></span>
                <div className="flex-1 bg-slate-700 rounded-md h-5 ml-2"></div>
              </div>
              {/* Mini stat row */}
              <div className="grid grid-cols-3 gap-3 mb-4">
                {[
                  { label: 'Tasks done', val: '248', color: 'bg-indigo-500' },
                  { label: 'On leave', val: '12', color: 'bg-amber-500' },
                  { label: 'Pending', val: '5', color: 'bg-teal-500' },
                ].map((s) => (
                  <div key={s.label} className="bg-slate-800 rounded-xl p-3">
                    <div className={`w-6 h-1.5 ${s.color} rounded mb-2`}></div>
                    <p className="text-white text-lg font-bold">{s.val}</p>
                    <p className="text-slate-400 text-xs">{s.label}</p>
                  </div>
                ))}
              </div>
              {/* Mini bar chart */}
              <div className="bg-slate-800 rounded-xl p-4 mb-3">
                <p className="text-slate-400 text-xs mb-3">Performance trend</p>
                <div className="flex items-end gap-2 h-16">
                  {[40, 65, 50, 80, 60, 90, 75, 95, 70, 85, 78, 100].map((h, i) => (
                    <div
                      key={i}
                      className="flex-1 rounded-sm bg-indigo-500 opacity-80"
                      style={{ height: `${h}%` }}
                    />
                  ))}
                </div>
              </div>
              {/* Mini user list */}
              <div className="space-y-2">
                {[
                  { name: 'Alice M.', role: 'Manager', status: 'Active' },
                  { name: 'John K.', role: 'Analyst', status: 'In meeting' },
                ].map((u) => (
                  <div key={u.name} className="flex items-center gap-3 bg-slate-800 rounded-xl px-3 py-2">
                    <div className="w-7 h-7 bg-indigo-600 rounded-lg flex items-center justify-center text-white text-xs font-bold">
                      {u.name[0]}
                    </div>
                    <div className="flex-1">
                      <p className="text-white text-xs font-semibold">{u.name}</p>
                      <p className="text-slate-400 text-xs">{u.role}</p>
                    </div>
                    <span className="text-xs px-2 py-0.5 bg-slate-700 text-slate-300 rounded-full">{u.status}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Trusted-by bar ── */}
      <div className="border-y border-slate-100 bg-slate-50 py-8">
        <div className="max-w-7xl mx-auto px-6">
          <p className="text-center text-xs font-semibold text-slate-400 uppercase tracking-widest mb-6">
            Trusted by teams across industries
          </p>
          <div className="flex flex-wrap justify-center items-center gap-10">
            {['Finance Corp', 'HealthTech Ltd', 'EduGroup', 'RetailPlus', 'BuildCo'].map((name) => (
              <div key={name} className="flex items-center gap-2 text-slate-400">
                <Building2 className="w-4 h-4" />
                <span className="text-sm font-semibold">{name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Features ── */}
      <section id="features" className="max-w-7xl mx-auto px-6 py-24">
        <div className="text-center mb-14">
          <span className="text-xs font-bold uppercase tracking-widest text-indigo-600">Features</span>
          <h2 className="text-4xl font-extrabold text-slate-900 mt-2 mb-4">
            Everything your workforce needs
          </h2>
          <p className="text-slate-500 max-w-xl mx-auto">
            From daily task tracking to enterprise-wide analytics — one platform, every capability.
          </p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[
            {
              icon: Users, color: 'bg-indigo-100 text-indigo-600',
              title: 'User management',
              desc: 'Role-based access control for admins, managers, analysts and employees with full audit trails.',
            },
            {
              icon: BarChart3, color: 'bg-violet-100 text-violet-600',
              title: 'Real-time analytics',
              desc: 'Live dashboards, performance metrics and visual trend reports updated every second.',
            },
            {
              icon: TrendingUp, color: 'bg-teal-100 text-teal-600',
              title: 'AI decision support',
              desc: 'Smart recommendations and pattern detection to help managers make faster, better decisions.',
            },
            {
              icon: Clock, color: 'bg-amber-100 text-amber-600',
              title: 'Leave & day-off management',
              desc: 'Streamlined day-off requests, approval workflows and leave balance tracking in one place.',
            },
            {
              icon: Database, color: 'bg-blue-100 text-blue-600',
              title: 'Performance data',
              desc: 'Centralised employee performance records with historical comparisons and KPI tracking.',
            },
            {
              icon: Shield, color: 'bg-green-100 text-green-600',
              title: 'Security & compliance',
              desc: 'Enterprise-grade encryption, comprehensive audit logging and GDPR-ready data handling.',
            },
          ].map((f) => (
            <div
              key={f.title}
              className="group p-6 bg-white border border-slate-200 rounded-2xl hover:border-indigo-300 hover:shadow-lg transition-all duration-200"
            >
              <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-5 ${f.color}`}>
                <f.icon className="w-6 h-6" />
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">{f.title}</h3>
              <p className="text-slate-500 text-sm leading-relaxed">{f.desc}</p>
              <div className="mt-4 flex items-center gap-1 text-indigo-600 text-sm font-semibold opacity-0 group-hover:opacity-100 transition-opacity">
                Learn more <ArrowRight className="w-4 h-4" />
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Roles section ── */}
      <section id="roles" className="bg-slate-50 border-y border-slate-200 py-24">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-14">
            <span className="text-xs font-bold uppercase tracking-widest text-indigo-600">Roles</span>
            <h2 className="text-4xl font-extrabold text-slate-900 mt-2 mb-4">
              Built for every level of your organisation
            </h2>
            <p className="text-slate-500 max-w-xl mx-auto">
              Each role gets a personalised experience with the tools and data they actually need.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                role: 'Admin',
                icon: Shield,
                color: 'bg-purple-100 text-purple-700 border-purple-200',
                accent: 'text-purple-700',
                perks: ['Full system control', 'User management', 'Audit logs', 'All analytics'],
              },
              {
                role: 'Manager',
                icon: Users,
                color: 'bg-blue-100 text-blue-700 border-blue-200',
                accent: 'text-blue-700',
                perks: ['Team oversight', 'Approve leave', 'Performance reports', 'Task assignment'],
              },
              {
                role: 'Analyst',
                icon: Activity,
                color: 'bg-teal-100 text-teal-700 border-teal-200',
                accent: 'text-teal-700',
                perks: ['Deep data access', 'Custom reports', 'Trend analysis', 'Export data'],
              },
              {
                role: 'Employee',
                icon: Award,
                color: 'bg-amber-100 text-amber-700 border-amber-200',
                accent: 'text-amber-700',
                perks: ['My tasks', 'Request leave', 'View performance', 'Personal reports'],
              },
            ].map((r) => (
              <div key={r.role} className="bg-white rounded-2xl border border-slate-200 p-6 hover:shadow-md transition-shadow">
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-4 border ${r.color}`}>
                  <r.icon className="w-6 h-6" />
                </div>
                <h3 className={`text-xl font-bold mb-4 ${r.accent}`}>{r.role}</h3>
                <ul className="space-y-2">
                  {r.perks.map((p) => (
                    <li key={p} className="flex items-center gap-2 text-sm text-slate-600">
                      <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                      {p}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Stats banner ── */}
      <section id="stats" className="bg-indigo-600 py-20">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid md:grid-cols-4 gap-8 text-center text-white">
            {[
              { icon: Users, number: '10,000+', label: 'Active users' },
              { icon: Globe, number: '40+', label: 'Organisations' },
              { icon: Star, number: '95%', label: 'Satisfaction rate' },
              { icon: Clock, number: '24/7', label: 'Support available' },
            ].map((s) => (
              <div key={s.label} className="space-y-2">
                <s.icon className="w-8 h-8 mx-auto text-indigo-200" />
                <div className="text-4xl font-extrabold">{s.number}</div>
                <div className="text-indigo-200 font-medium">{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA strip ── */}
      <section className="max-w-4xl mx-auto px-6 py-24 text-center">
        <div className="bg-slate-900 rounded-3xl px-8 py-14">
          <span className="inline-flex items-center gap-2 px-4 py-1.5 bg-indigo-500/20 border border-indigo-400/30 rounded-full text-xs font-semibold text-indigo-300 uppercase tracking-wider mb-6">
            <Lock className="w-3.5 h-3.5" /> Secure & enterprise-ready
          </span>
          <h2 className="text-3xl font-extrabold text-white mb-4">
            Ready to transform your workforce?
          </h2>
          <p className="text-slate-400 mb-8 max-w-md mx-auto">
            Join thousands of organisations already using CodePulse Analytics to make smarter, faster decisions.
          </p>
          <Link
            to="/login"
            className="inline-flex items-center gap-2 px-8 py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl transition-colors shadow-lg shadow-indigo-900/40"
          >
            Get started today <ChevronRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="border-t border-slate-200 bg-slate-50">
        <div className="max-w-7xl mx-auto px-6 py-10">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-4 h-4 text-white" />
              </div>
              <span className="text-base font-bold text-slate-900">
                CodePulse <span className="text-indigo-600">Analytics</span>
              </span>
            </div>
            <p className="text-sm text-slate-400">
              © 2026 CodePulse Analytics. All rights reserved.
            </p>
            <div className="flex items-center gap-6 text-sm text-slate-500">
              {['Privacy', 'Terms', 'Support'].map((l) => (
                <a key={l} href="#" className="hover:text-indigo-600 transition-colors">{l}</a>
              ))}
            </div>
          </div>
        </div>
      </footer>

    </div>
  );
}