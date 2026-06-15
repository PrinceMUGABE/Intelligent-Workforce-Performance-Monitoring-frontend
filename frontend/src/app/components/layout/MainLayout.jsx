import React, { useState } from 'react';
import { Outlet, useNavigate } from 'react-router';
import { useAuth } from './app/contexts/AuthContext';
import {
  BarChart3,
  FileText,
  Home,
  LogOut,
  Menu,
  Settings,
  Shield,
  TrendingUp,
  Users,
  X,
} from 'lucide-react';

export const MainLayout = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navigation = [
    { name: 'Dashboard', icon: Home, path: '/dashboard', roles: ['admin', 'manager', 'employee', 'data-analyst'] },
    { name: 'Users', icon: Users, path: '/users', roles: ['admin'] },
    { name: 'Performance', icon: TrendingUp, path: '/performance', roles: ['admin', 'manager', 'data-analyst'] },
    { name: 'Analytics', icon: BarChart3, path: '/analytics', roles: ['admin', 'manager', 'data-analyst'] },
    { name: 'Reports', icon: FileText, path: '/reports', roles: ['admin', 'manager', 'employee', 'data-analyst'] },
    { name: 'Audit Logs', icon: Shield, path: '/audit-logs', roles: ['admin'] },
  ];

  const filteredNavigation = navigation.filter(item => 
    item.roles.includes(user?.role || '')
  );

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Top Navigation */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-4">
            <button
              className="md:hidden p-2 rounded-md hover:bg-slate-100"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              {sidebarOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-sky-600 to-indigo-600" />
              <span className="text-xl text-slate-900">Workforce Analytics</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <div className="relative">
              <button className="flex items-center gap-2 p-2 rounded-md hover:bg-slate-100">
                <div className="h-8 w-8 rounded-full bg-gradient-to-br from-sky-500 to-indigo-500 text-white flex items-center justify-center">
                  {user?.name?.charAt(0).toUpperCase()}
                </div>
                <div className="text-left hidden md:block">
                  <div className="text-sm text-slate-900">{user?.name}</div>
                  <div className="text-xs text-slate-500 capitalize">{user?.role}</div>
                </div>
              </button>
              
              {/* Dropdown menu */}
              <div className="absolute right-0 mt-2 w-56 bg-white rounded-md shadow-lg border border-slate-200 hidden group-hover:block">
                <div className="py-2">
                  <div className="px-4 py-2 text-sm font-medium text-slate-900">My Account</div>
                  <div className="border-t border-slate-200"></div>
                  <button 
                    className="flex items-center w-full px-4 py-2 text-sm text-slate-700 hover:bg-slate-100"
                    onClick={() => navigate('/profile')}
                  >
                    <Settings className="mr-2 h-4 w-4" />
                    Profile Settings
                  </button>
                  <button 
                    className="flex items-center w-full px-4 py-2 text-sm text-slate-700 hover:bg-slate-100"
                    onClick={handleLogout}
                  >
                    <LogOut className="mr-2 h-4 w-4" />
                    Logout
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside className={`${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        } md:translate-x-0 fixed md:sticky top-[57px] left-0 z-30 h-[calc(100vh-57px)] w-64 bg-white border-r border-slate-200 transition-transform duration-200 ease-in-out overflow-y-auto`}>
          <nav className="p-4 space-y-1">
            {filteredNavigation.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.path}
                  className="w-full flex items-center justify-start gap-3 p-2 rounded-md hover:bg-sky-50 hover:text-sky-700 text-slate-700"
                  onClick={() => {
                    navigate(item.path);
                    setSidebarOpen(false);
                  }}
                >
                  <Icon className="h-5 w-5" />
                  {item.name}
                </button>
              );
            })}
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
};