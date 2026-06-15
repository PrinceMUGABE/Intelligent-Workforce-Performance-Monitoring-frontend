import {
  Routes,
  Route,
  NavLink,
  useNavigate,
} from "react-router";
import { useAuth } from "../context/auth-context";
import {
  BarChart3,
  LayoutDashboard,
  Users,
  FileText,
  Settings,
  LogOut,
  Menu,
  X,
  TrendingUp,
  Database,
  History,
  UserCircle,
  ChevronDown,
  Building2,
  CheckSquare,
  CalendarClock,
  Shield,
  Activity,
} from "lucide-react";
import { useState, useEffect } from "react";
import Dashboard from "./pages/dashboard";
import UsersManagement from "./pages/users-management";
import PerformanceData from "./pages/performance-data";
import Reports from "./pages/reports";
import Analytics from "./pages/analytics";
import AuditLogs from "./pages/audit-logs";
import ProfilePage from "./pages/profile-page";
import DepartmentsPage from "./pages/departments";
import TasksPage from "./pages/tasks";
import DayOffChangeRequestManagement from "./pages/Day-offChange";

const navigation = {
  admin: [
    { name: "Dashboard", path: "", icon: LayoutDashboard, description: "Overview & metrics" },
    { name: "User Management", path: "users", icon: Users, description: "Manage team members" },
    { name: "Departments", path: "departments", icon: Building2, description: "Organizational units" },
    { name: "Tasks & Assignments", path: "tasks", icon: CheckSquare, description: "Project tracking" },
    { name: "Day-Off Requests", path: "day-off-requests", icon: CalendarClock, description: "Leave management" },
    { name: "Performance Data", path: "performance", icon: TrendingUp, description: "Performance metrics" },
    { name: "Analytics", path: "analytics", icon: BarChart3, description: "Data insights" },
    { name: "Reports", path: "reports", icon: FileText, description: "Generated reports" },
    { name: "Audit Logs", path: "audit", icon: History, description: "System activity" },
  ],
  manager: [
    { name: "Dashboard", path: "", icon: LayoutDashboard, description: "Team overview" },
    { name: "Team Management", path: "users", icon: Users, description: "Manage your team" },
    { name: "Tasks & Assignments", path: "tasks", icon: CheckSquare, description: "Track team tasks" },
    { name: "Day-Off Requests", path: "day-off-requests", icon: CalendarClock, description: "Approve leave" },
    { name: "Performance Data", path: "performance", icon: TrendingUp, description: "Team performance" },
    { name: "Analytics", path: "analytics", icon: BarChart3, description: "Team insights" },
    { name: "Reports", path: "reports", icon: FileText, description: "Team reports" },
    { name: "Audit Logs", path: "audit", icon: History, description: "Activity logs" },
  ],
  employee: [
    { name: "Dashboard", path: "", icon: LayoutDashboard, description: "Your workspace" },
    { name: "My Tasks", path: "tasks", icon: CheckSquare, description: "Task management" },
    { name: "Request Day-Off", path: "day-off-requests", icon: CalendarClock, description: "Leave requests" },
    { name: "My Performance", path: "performance", icon: TrendingUp, description: "Your metrics" },
    { name: "Reports", path: "reports", icon: FileText, description: "Your reports" },
    { name: "Audit Logs", path: "audit", icon: History, description: "Your activity" },
  ],
  analyst: [
    { name: "Dashboard", path: "", icon: LayoutDashboard, description: "Analytics hub" },
    { name: "Analytics", path: "analytics", icon: BarChart3, description: "Deep insights" },
    { name: "Performance Data", path: "performance", icon: Database, description: "All metrics" },
    { name: "Day-Off Requests", path: "day-off-requests", icon: CalendarClock, description: "Leave analytics" },
    { name: "Reports", path: "reports", icon: FileText, description: "Custom reports" },
    { name: "Audit Logs", path: "audit", icon: History, description: "System logs" },
  ],
};

function useGreeting() {
  const [greeting, setGreeting] = useState("");
  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const update = () => {
      const now = new Date();
      const hour = now.getHours();
      setCurrentTime(now);
      if (hour >= 5 && hour < 12) setGreeting("Good morning");
      else if (hour >= 12 && hour < 17) setGreeting("Good afternoon");
      else setGreeting("Good evening");
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  const formattedTime = currentTime.toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

  const formattedDate = currentTime.toLocaleDateString([], {
    weekday: "short",
    month: "short",
    day: "numeric",
  });

  return { greeting, formattedTime, formattedDate };
}

export default function DashboardLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [profileDropdownOpen, setProfileDropdownOpen] = useState(false);

  const { greeting, formattedTime, formattedDate } = useGreeting();

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024) setSidebarOpen(false);
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (profileDropdownOpen && !event.target.closest(".profile-dropdown")) {
        setProfileDropdownOpen(false);
      }
    };
    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, [profileDropdownOpen]);

  if (!user) return null;

  const userNavigation = navigation[user.role] || navigation.employee;

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const handleNavClick = () => setSidebarOpen(false);

  const getRoleColor = (role) => {
    const colors = {
      admin: "text-purple-600 bg-purple-100",
      manager: "text-blue-600 bg-blue-100",
      analyst: "text-green-600 bg-green-100",
      employee: "text-slate-600 bg-slate-100",
    };
    return colors[role] || colors.employee;
  };

  const getRoleIcon = (role) => {
    const icons = { admin: Shield, manager: Users, analyst: Activity, employee: UserCircle };
    const Icon = icons[role] || UserCircle;
    return <Icon className="w-4 h-4" />;
  };

  // Avatar initials from full name
  const getInitials = (name = "") => {
    const parts = name.trim().split(" ");
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return (parts[0]?.[0] || "U").toUpperCase();
  };

  return (
    // Root: full viewport height, no overflow — everything is locked
    <div className="h-screen w-screen overflow-hidden flex flex-col bg-gradient-to-br from-slate-50 via-white to-slate-50">

      {/* ── Top Navigation Bar (fixed height, never scrolls) ── */}
      <nav className="flex-shrink-0 bg-white/80 backdrop-blur-md border-b border-slate-200/60 shadow-sm z-50">
        <div className="px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">

            {/* Left: Logo + mobile hamburger */}
            <div className="flex items-center gap-4">
              <button
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="lg:hidden p-2 rounded-xl hover:bg-slate-100 transition-all duration-200"
                aria-label="Toggle menu"
              >
                {sidebarOpen ? (
                  <X className="w-6 h-6 text-slate-700" />
                ) : (
                  <Menu className="w-6 h-6 text-slate-700" />
                )}
              </button>

              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-violet-600 rounded-xl flex items-center justify-center shadow-lg shadow-indigo-200">
                  <BarChart3 className="w-6 h-6 text-white" />
                </div>
                <div className="hidden sm:block">
                  <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">
                    CodePulse Analytics
                  </h1>
                  <p className="text-xs text-slate-500">Intelligent Workforce Monitoring</p>
                </div>
              </div>
            </div>

            {/* Center: Greeting + live clock */}
            <div className="hidden md:flex flex-col items-center justify-center">
              <p className="text-sm font-semibold text-slate-800">
                {greeting},{" "}
                <span className="text-indigo-600">{user.full_name}</span> 👋
              </p>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="text-xs font-mono text-slate-500 tabular-nums">
                  {formattedTime}
                </span>
                <span className="text-xs text-slate-400">·</span>
                <span className="text-xs text-slate-400">{formattedDate}</span>
              </div>
            </div>

            {/* Right: Profile dropdown */}
            <div className="relative profile-dropdown">
              <button
                onClick={() => setProfileDropdownOpen(!profileDropdownOpen)}
                className="flex items-center gap-3 p-2 pr-3 rounded-xl hover:bg-slate-100 transition-all duration-200"
              >
                <div className="w-9 h-9 bg-gradient-to-br from-indigo-500 to-violet-600 rounded-xl flex items-center justify-center text-white font-semibold shadow-md text-sm">
                  {getInitials(user.full_name)}
                </div>
                <div className="hidden lg:block text-left">
                  <div className="text-sm font-semibold text-slate-900">{user.full_name}</div>
                  <div className={`text-xs font-medium capitalize inline-flex items-center gap-1 px-2 py-0.5 rounded-full ${getRoleColor(user.role)}`}>
                    {getRoleIcon(user.role)}
                    {user.role.replace("_", " ")}
                  </div>
                </div>
                <ChevronDown className={`w-4 h-4 text-slate-400 transition-transform hidden lg:block ${profileDropdownOpen ? "rotate-180" : ""}`} />
              </button>

              {profileDropdownOpen && (
                <>
                  <div
                    className="fixed inset-0 z-40 lg:hidden"
                    onClick={() => setProfileDropdownOpen(false)}
                  />
                  <div className="absolute right-0 mt-2 w-64 bg-white rounded-2xl shadow-2xl border border-slate-200 py-2 z-50">
                    {/* Profile header */}
                    <div className="px-4 py-3 border-b border-slate-100">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-violet-600 rounded-xl flex items-center justify-center text-white font-bold text-lg shadow-md">
                          {getInitials(user.full_name)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="font-semibold text-slate-900 truncate">{user.full_name}</div>
                          <div className="text-xs text-slate-500 truncate">{user.email}</div>
                        </div>
                      </div>
                      <div className={`mt-2 inline-flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-medium ${getRoleColor(user.role)}`}>
                        {getRoleIcon(user.role)}
                        {user.role.replace("_", " ")}
                      </div>
                    </div>

                    {/* Mobile greeting in dropdown */}
                    <div className="md:hidden px-4 py-3 border-b border-slate-100">
                      <p className="text-sm font-semibold text-slate-800">
                        {greeting}, {user.full_name} 👋
                      </p>
                      <p className="text-xs font-mono text-slate-500 tabular-nums mt-0.5">
                        {formattedTime} · {formattedDate}
                      </p>
                    </div>

                    <div className="py-2">
                      <button
                        onClick={() => {
                          navigate("/dashboard/profile");
                          setProfileDropdownOpen(false);
                        }}
                        className="w-full px-4 py-2.5 text-left text-sm hover:bg-slate-50 flex items-center gap-3 transition-colors"
                      >
                        <div className="w-8 h-8 bg-indigo-50 rounded-lg flex items-center justify-center">
                          <UserCircle className="w-4 h-4 text-indigo-600" />
                        </div>
                        <div>
                          <div className="font-medium text-slate-900">My Profile</div>
                          <div className="text-xs text-slate-500">View and edit profile</div>
                        </div>
                      </button>

                      <button
                        onClick={() => {
                          setProfileDropdownOpen(false);
                          navigate("/dashboard");
                        }}
                        className="w-full px-4 py-2.5 text-left text-sm hover:bg-slate-50 flex items-center gap-3 transition-colors"
                      >
                        <div className="w-8 h-8 bg-slate-50 rounded-lg flex items-center justify-center">
                          <Settings className="w-4 h-4 text-slate-600" />
                        </div>
                        <div>
                          <div className="font-medium text-slate-900">Settings</div>
                          <div className="text-xs text-slate-500">Preferences & privacy</div>
                        </div>
                      </button>
                    </div>

                    <hr className="my-2 border-slate-100" />

                    <button
                      onClick={handleLogout}
                      className="w-full px-4 py-2.5 text-left text-sm hover:bg-red-50 text-red-600 flex items-center gap-3 transition-colors rounded-b-2xl"
                    >
                      <div className="w-8 h-8 bg-red-50 rounded-lg flex items-center justify-center">
                        <LogOut className="w-4 h-4 text-red-600" />
                      </div>
                      <div>
                        <div className="font-medium">Sign Out</div>
                        <div className="text-xs text-red-500">Logout from account</div>
                      </div>
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* ── Body row: sidebar + main (fills remaining height exactly) ── */}
      <div className="flex flex-1 min-h-0 relative">

        {/* Mobile overlay */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/30 z-40 lg:hidden backdrop-blur-sm"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* ── Sidebar (fixed height, internal nav scrolls, footer pinned) ── */}
        <aside
          className={`
            fixed lg:static inset-y-0 left-0 z-50
            w-72 flex-shrink-0
            bg-white/90 backdrop-blur-md border-r border-slate-200/60
            flex flex-col
            transform transition-all duration-300 ease-in-out
            ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
            lg:translate-x-0 lg:transform-none
            shadow-2xl lg:shadow-none
            h-full
          `}
        >
          {/* Mobile sidebar header */}
          <div className="lg:hidden flex-shrink-0 flex items-center justify-between p-4 border-b border-slate-200/60">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-indigo-600 to-violet-600 rounded-xl flex items-center justify-center shadow-lg">
                <BarChart3 className="w-6 h-6 text-white" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-900">CodePulse</h2>
                <p className="text-xs text-slate-500">Analytics Platform</p>
              </div>
            </div>
            <button
              onClick={() => setSidebarOpen(false)}
              className="p-2 rounded-xl hover:bg-slate-100 transition-all"
              aria-label="Close menu"
            >
              <X className="w-5 h-5 text-slate-600" />
            </button>
          </div>

          {/* Desktop user info (top of sidebar) */}
          <div className="hidden lg:flex flex-shrink-0 items-center gap-3 px-5 py-5 border-b border-slate-200/60">
            <div className="w-11 h-11 bg-gradient-to-br from-indigo-500 to-violet-600 rounded-xl flex items-center justify-center text-white font-bold text-base shadow-md">
              {getInitials(user.full_name)}
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-semibold text-slate-900 truncate text-sm">{user.full_name}</div>
              <div className={`mt-1 inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium ${getRoleColor(user.role)}`}>
                {getRoleIcon(user.role)}
                <span className="capitalize">{user.role.replace("_", " ")}</span>
              </div>
            </div>
          </div>

          {/* Nav links — scrollable middle section */}
          <nav className="flex-1 overflow-y-auto px-4 py-5 space-y-1
            scrollbar-thin scrollbar-thumb-slate-200 scrollbar-track-transparent">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3 px-3">
              Navigation
            </p>
            {userNavigation.map((item) => (
              <NavLink
                key={item.path}
                to={`/dashboard/${item.path}`}
                end={item.path === ""}
                onClick={handleNavClick}
                className={({ isActive }) =>
                  `group flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 ${
                    isActive
                      ? "bg-gradient-to-r from-indigo-500 to-violet-600 text-white shadow-lg shadow-indigo-200"
                      : "text-slate-700 hover:bg-slate-100 hover:translate-x-1"
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 transition-all ${
                      isActive ? "bg-white/20" : "bg-slate-100 group-hover:bg-slate-200"
                    }`}>
                      <item.icon className={`w-4 h-4 ${isActive ? "text-white" : "text-slate-600"}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className={`font-medium text-sm truncate ${isActive ? "text-white" : "text-slate-900"}`}>
                        {item.name}
                      </div>
                      <div className={`text-xs truncate ${isActive ? "text-white/75" : "text-slate-500"}`}>
                        {item.description}
                      </div>
                    </div>
                  </>
                )}
              </NavLink>
            ))}
          </nav>

          {/* ── Sidebar footer: user card + logout (always visible, pinned) ── */}
          <div className="flex-shrink-0 border-t border-slate-200/60 p-4 space-y-3">
            {/* User card */}
            <div className="flex items-center gap-3 px-3 py-3 bg-gradient-to-r from-indigo-50 to-violet-50 rounded-xl border border-indigo-100">
              <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-violet-600 rounded-xl flex items-center justify-center text-white font-bold text-sm shadow-md flex-shrink-0">
                {getInitials(user.full_name)}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-slate-900 truncate">{user.full_name}</p>
                <p className="text-xs text-slate-500 truncate">{user.email || user.work_mail_address}</p>
              </div>
            </div>

            {/* Logout button */}
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-3 px-4 py-3 rounded-xl bg-red-50 hover:bg-red-100 border border-red-100 hover:border-red-200 text-red-600 transition-all duration-200 group"
            >
              <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center shadow-sm group-hover:shadow flex-shrink-0 transition-all">
                <LogOut className="w-4 h-4 text-red-500" />
              </div>
              <div className="text-left">
                <p className="text-sm font-semibold text-red-600">Sign Out</p>
                <p className="text-xs text-red-400">End your session</p>
              </div>
            </button>
          </div>
        </aside>

        {/* ── Main content area: fixed frame, inner content scrollable ── */}
        <main className="flex-1 min-w-0 min-h-0 flex flex-col bg-slate-50/50">
          {/* Scrollable viewport — both axes */}
          <div className="flex-1 overflow-auto p-4 sm:p-6 lg:p-8
            scrollbar-thin scrollbar-thumb-slate-300 scrollbar-track-slate-100">
            {/* min-w ensures wide content (tables, charts) triggers horizontal scroll
                instead of squishing */}
            <div className="min-w-max-content w-full">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/users" element={<UsersManagement />} />
                <Route path="/performance" element={<PerformanceData />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="/audit" element={<AuditLogs />} />
                <Route path="/profile" element={<ProfilePage />} />
                <Route path="/departments" element={<DepartmentsPage />} />
                <Route path="/tasks" element={<TasksPage />} />
                <Route path="/day-off-requests/*" element={<DayOffChangeRequestManagement />} />
              </Routes>
            </div>
          </div>
        </main>

      </div>
    </div>
  );
}