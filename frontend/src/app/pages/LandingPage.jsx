import React from 'react';
import { useNavigate } from 'react-router';
import { Activity, BarChart3, Shield, TrendingUp, Users, Zap } from 'lucide-react';

export const LandingPage = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: <Activity className="h-8 w-8 text-sky-600" />,
      title: 'Real-time Monitoring',
      description: 'Track workforce performance metrics in real-time with comprehensive dashboards.'
    },
    {
      icon: <BarChart3 className="h-8 w-8 text-indigo-600" />,
      title: 'Advanced Analytics',
      description: 'Gain insights with powerful analytics and data visualization tools.'
    },
    {
      icon: <TrendingUp className="h-8 w-8 text-cyan-600" />,
      title: 'Performance Trends',
      description: 'Identify patterns and trends to make data-driven decisions.'
    },
    {
      icon: <Users className="h-8 w-8 text-slate-600" />,
      title: 'Team Management',
      description: 'Manage teams effectively with role-based access control.'
    },
    {
      icon: <Shield className="h-8 w-8 text-sky-700" />,
      title: 'Secure & Compliant',
      description: 'Enterprise-grade security with comprehensive audit logging.'
    },
    {
      icon: <Zap className="h-8 w-8 text-indigo-500" />,
      title: 'Decision Support',
      description: 'Get intelligent recommendations based on performance data.'
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-sky-50 to-indigo-50">
      {/* Hero Section */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-6xl mb-6 bg-gradient-to-r from-slate-900 via-sky-900 to-indigo-900 bg-clip-text text-transparent">
            Workforce Performance Analytics
          </h1>
          <p className="text-xl text-slate-600 max-w-3xl mx-auto mb-8">
            Empower your organization with intelligent workforce monitoring and analytics.
            Make data-driven decisions to optimize performance and productivity.
          </p>
          <div className="flex gap-4 justify-center">
            <button
              onClick={() => navigate('/login')}
              className="px-8 py-6 text-lg bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white rounded-md"
            >
              Get Started
            </button>
            <button
              onClick={() => navigate('/login')}
              className="px-8 py-6 text-lg border-2 border-sky-600 text-sky-700 hover:bg-sky-50 rounded-md"
            >
              Sign In
            </button>
          </div>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mt-16">
          {features.map((feature, index) => (
            <div key={index} className="border border-slate-200 hover:shadow-lg transition-shadow bg-white/80 backdrop-blur rounded-lg p-6">
              <div className="mb-6">
                <div className="mb-4">{feature.icon}</div>
                <h3 className="text-lg font-semibold text-slate-900">{feature.title}</h3>
                <p className="text-slate-600 mt-2">
                  {feature.description}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Stats Section */}
        <div className="mt-20 grid md:grid-cols-3 gap-8 text-center">
          <div>
            <div className="text-5xl mb-2 bg-gradient-to-r from-sky-600 to-indigo-600 bg-clip-text text-transparent">500+</div>
            <div className="text-slate-600">Organizations</div>
          </div>
          <div>
            <div className="text-5xl mb-2 bg-gradient-to-r from-sky-600 to-indigo-600 bg-clip-text text-transparent">50K+</div>
            <div className="text-slate-600">Users</div>
          </div>
          <div>
            <div className="text-5xl mb-2 bg-gradient-to-r from-sky-600 to-indigo-600 bg-clip-text text-transparent">99.9%</div>
            <div className="text-slate-600">Uptime</div>
          </div>
        </div>
      </div>
    </div>
  );
};