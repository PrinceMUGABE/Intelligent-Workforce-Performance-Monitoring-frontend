/* eslint-disable no-unused-vars */
import { useState, useEffect } from 'react';
import { useAuth } from '../../context/auth-context';
import { 
  Users, TrendingUp, Award, AlertTriangle, ArrowUp, ArrowDown,
  Loader2, RefreshCw, Clock, CheckCircle, XCircle, Calendar,
  Target, Activity, Zap, TrendingDown, Bell, Star, BarChart3,
  LineChart, Download, Filter, Info, ChevronRight,
  Settings, UserCheck, UserX, Briefcase, Timer, Award as Trophy,
  TrendingUp as TrendUp, AlertCircle, Check, Clock as TimeIcon
} from 'lucide-react';
import { 
  BarChart, Bar, PieChart, Line, Pie, Cell, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  ComposedChart, Scatter
} from 'recharts';
import { toast } from 'sonner';

const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6', '#14b8a6'];

const ICON_MAP = {
  'Users': Users,
  'TrendingUp': TrendingUp,
  'Award': Award,
  'AlertTriangle': AlertTriangle,
  'Target': Target,
  'Activity': Activity,
  'Zap': Zap,
  'CheckCircle': CheckCircle,
  'Clock': Clock,
  'Calendar': Calendar,
  'Star': Star,
  'BarChart': BarChart3,
  'PieChart': PieChart,
  'LineChart': LineChart,
  'Timer': Timer,
  'Trophy': Trophy,
  'UserCheck': UserCheck,
  'UserX': UserX,
  'Briefcase': Briefcase,
  'AlertCircle': AlertCircle,
  'Check': Check,
  'TimeIcon': TimeIcon,
  'TrendUp': TrendUp,
  'TrendingDown': TrendingDown,
  'Bell': Bell,
  'Settings': Settings
};

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-4 rounded-lg shadow-lg border border-slate-200">
        <p className="font-medium text-slate-900">{label}</p>
        {payload.map((entry, index) => (
          <p key={index} className="text-sm" style={{ color: entry.color }}>
            {entry.name}: {entry.value}{entry.unit || ''}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

const ChartInfo = ({ title, description, insights }) => {
  const [showInfo, setShowInfo] = useState(false);
  
  return (
    <div className="relative">
      <div className="flex items-center gap-2 mb-2">
        <h3 className="text-lg font-semibold text-slate-900">{title}</h3>
        <button
          onClick={() => setShowInfo(!showInfo)}
          className="p-1 hover:bg-slate-100 rounded-full transition-colors"
        >
          <Info className="w-4 h-4 text-slate-500" />
        </button>
      </div>
      {showInfo && (
        <div className="absolute z-10 bg-white p-4 rounded-lg shadow-lg border border-slate-200 w-64">
          <p className="text-sm text-slate-600 mb-2">{description}</p>
          {insights && insights.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-slate-700 mb-1">Key Insights:</p>
              <ul className="text-xs text-slate-600 list-disc pl-4">
                {insights.map((insight, i) => (
                  <li key={i}>{insight}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const StatCard = ({ stat }) => {
  const IconComponent = ICON_MAP[stat.icon] || Activity;
  const changeColor = stat.change_type === 'increase' ? 'text-emerald-600' : 
                     stat.change_type === 'decrease' ? 'text-red-600' : 'text-slate-600';
  const ChangeIcon = stat.change_type === 'increase' ? ArrowUp : 
                    stat.change_type === 'decrease' ? ArrowDown : null;
  
  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between mb-4">
        <div className={`w-12 h-12 rounded-lg flex items-center justify-center bg-${stat.color}-100 text-${stat.color}-600`}>
          <IconComponent className="w-6 h-6" />
        </div>
        {stat.change !== 0 && (
          <div className={`flex items-center gap-1 text-sm font-medium ${changeColor}`}>
            {ChangeIcon && <ChangeIcon className="w-4 h-4" />}
            {Math.abs(stat.change).toFixed(1)}%
          </div>
        )}
      </div>
      <div className="text-2xl font-bold text-slate-900">{stat.value}</div>
      <div className="text-sm text-slate-600 mt-1">{stat.title}</div>
      <p className="text-xs text-slate-500 mt-2">{stat.description}</p>
      
      {stat.target && (
        <div className="mt-3">
          <div className="flex justify-between text-xs mb-1">
            <span className="text-slate-600">Progress to target</span>
            <span className="font-medium text-slate-900">{stat.progress?.toFixed(0)}%</span>
          </div>
          <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div 
              className={`h-full bg-${stat.color}-500 rounded-full`}
              style={{ width: `${Math.min(100, stat.progress || 0)}%` }}
            />
          </div>
        </div>
      )}
      
      {stat.trend_data && stat.trend_data.length > 0 && (
        <div className="mt-3 h-8">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={stat.trend_data}>
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke={`var(--${stat.color}-500)`} 
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

const ActivityItem = ({ activity }) => {
  const statusColors = {
    success: 'bg-emerald-100 text-emerald-600',
    warning: 'bg-amber-100 text-amber-600',
    error: 'bg-red-100 text-red-600',
    info: 'bg-blue-100 text-blue-600'
  };
  
  return (
    <div className="flex items-start gap-3 p-3 hover:bg-slate-50 rounded-lg transition-colors">
      <div className={`w-8 h-8 rounded-full ${statusColors[activity.status]} flex items-center justify-center text-xs font-medium`}>
        {activity.user_avatar || activity.user[0]}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-slate-900">
          <span className="font-medium">{activity.user}</span> {activity.action}
        </p>
        <p className="text-xs text-slate-500 mt-1">{activity.time_ago}</p>
      </div>
      {activity.metadata?.method && (
        <span className="text-xs px-2 py-1 bg-slate-100 rounded text-slate-600">
          {activity.metadata.method}
        </span>
      )}
    </div>
  );
};

const TaskItem = ({ task }) => {
  const priorityColors = {
    urgent: 'bg-red-100 text-red-800 border-red-200',
    high: 'bg-orange-100 text-orange-800 border-orange-200',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    low: 'bg-green-100 text-green-800 border-green-200'
  };
  
  return (
    <div className="flex items-center gap-4 p-3 hover:bg-slate-50 rounded-lg transition-colors border border-slate-200">
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <h4 className="font-medium text-slate-900">{task.name}</h4>
          {task.is_overdue && (
            <span className="text-xs px-2 py-0.5 bg-red-100 text-red-800 rounded-full">
              Overdue
            </span>
          )}
        </div>
        <p className="text-xs text-slate-500 mb-2">{task.description}</p>
        <div className="flex items-center gap-4 text-xs">
          <span className="text-slate-600">Assigned to: {task.assigned_to}</span>
          <span className="text-slate-600">Due: {task.time_remaining}</span>
        </div>
        {task.progress > 0 && (
          <div className="mt-2">
            <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div 
                className="h-full bg-indigo-500 rounded-full"
                style={{ width: `${task.progress}%` }}
              />
            </div>
          </div>
        )}
      </div>
      <div className="flex flex-col items-end gap-2">
        <span className={`px-2 py-1 rounded text-xs font-medium border ${priorityColors[task.priority]}`}>
          {task.priority}
        </span>
        <span className="text-xs text-slate-500">{task.department}</span>
      </div>
    </div>
  );
};

const Alert = ({ alert, onDismiss }) => {
  const alertStyles = {
    info: 'bg-blue-50 border-blue-200 text-blue-800',
    warning: 'bg-amber-50 border-amber-200 text-amber-800',
    error: 'bg-red-50 border-red-200 text-red-800',
    success: 'bg-green-50 border-green-200 text-green-800'
  };
  
  const icons = {
    info: Bell,
    warning: AlertTriangle,
    error: XCircle,
    success: CheckCircle
  };
  
  const Icon = icons[alert.type] || Bell;
  
  return (
    <div className={`p-4 rounded-lg border ${alertStyles[alert.type]} flex items-start gap-3`}>
      <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" />
      <div className="flex-1">
        <div className="font-medium mb-1 flex items-center gap-2">
          {alert.title}
          {alert.priority === 'high' && (
            <span className="px-2 py-0.5 text-xs bg-red-100 text-red-700 rounded-full">High Priority</span>
          )}
        </div>
        <div className="text-sm opacity-90 mb-2">{alert.message}</div>
        <div className="flex items-center gap-3 text-xs">
          <span className="opacity-75">{alert.time_ago}</span>

        </div>
      </div>
      {onDismiss && (
        <button 
          onClick={() => onDismiss(alert.id)}
          className="text-slate-500 hover:text-slate-700"
        >
          <XCircle className="w-4 h-4" />
        </button>
      )}
    </div>
  );
};

const DepartmentCard = ({ dept }) => {
  return (
    <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
      <div className="flex items-center justify-between mb-3">
        <h4 className="font-semibold text-slate-900">{dept.name}</h4>
        <span className={`text-sm font-medium ${
          dept.performance_score >= 80 ? 'text-emerald-600' :
          dept.performance_score >= 60 ? 'text-amber-600' :
          'text-red-600'
        }`}>
          {dept.performance_score}%
        </span>
      </div>
      
      <div className="grid grid-cols-2 gap-3 mb-3">
        <div>
          <p className="text-xs text-slate-500">Employees</p>
          <p className="text-lg font-semibold text-slate-900">{dept.active_employees}/{dept.employee_count}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Completion</p>
          <p className="text-lg font-semibold text-slate-900">{dept.task_completion_rate}%</p>
        </div>
      </div>
      
      <div className="flex items-center gap-1 text-sm">
        <TrendingUp className={`w-4 h-4 ${dept.trend > 0 ? 'text-emerald-500' : 'text-red-500'}`} />
        <span className={dept.trend > 0 ? 'text-emerald-600' : 'text-red-600'}>
          {dept.trend > 0 ? '+' : ''}{dept.trend}%
        </span>
        <span className="text-xs text-slate-500 ml-1">vs last month</span>
      </div>
      
      {dept.top_performers && dept.top_performers.length > 0 && (
        <div className="mt-3 pt-3 border-t border-slate-200">
          <p className="text-xs font-medium text-slate-700 mb-2">Top Performers</p>
          {dept.top_performers.map((performer, i) => (
            <div key={i} className="flex items-center justify-between text-xs mb-1">
              <span className="text-slate-600">{performer.name}</span>
              <span className="font-medium text-slate-900">{performer.score}%</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const InsightCard = ({ insight }) => {
  const typeColors = {
    positive: 'bg-emerald-50 border-emerald-200 text-emerald-800',
    neutral: 'bg-blue-50 border-blue-200 text-blue-800',
    warning: 'bg-amber-50 border-amber-200 text-amber-800',
    info: 'bg-slate-50 border-slate-200 text-slate-800'
  };
  
  const Icon = ICON_MAP[insight.icon] || Info;
  
  return (
    <div className={`p-4 rounded-lg border ${typeColors[insight.type]}`}>
      <div className="flex items-start gap-3">
        <Icon className="w-5 h-5 flex-shrink-0" />
        <div>
          <h4 className="font-medium mb-1">{insight.title}</h4>
          <p className="text-sm opacity-90">{insight.message}</p>
        </div>
      </div>
    </div>
  );
};

const AchievementCard = ({ achievement }) => {
  return (
    <div className="flex items-center gap-3 p-4 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-lg border border-indigo-200">
      <div className="text-3xl">{achievement.icon}</div>
      <div>
        <div className="font-medium text-slate-900">{achievement.title}</div>
        <div className="text-sm text-slate-600">{achievement.description}</div>
        <div className="text-xs text-slate-500 mt-1">{achievement.earned_at}</div>
      </div>
    </div>
  );
};

export default function Dashboard() {
  const { user, api } = useAuth();
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [dashboardData, setDashboardData] = useState(null);
  const [dismissedAlerts, setDismissedAlerts] = useState([]);
  const [dateRange, setDateRange] = useState('week');

  useEffect(() => {
    if (user) {
      fetchDashboardData();
    }
  }, [user, dateRange]);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const response = await api.get(`http://127.0.0.1:8000/dashboard/?range=${dateRange}`);
      setDashboardData(response.data);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchDashboardData();
    setRefreshing(false);
    toast.success('Dashboard refreshed');
  };

  const handleDismissAlert = (alertId) => {
    setDismissedAlerts([...dismissedAlerts, alertId]);
  };

  if (!user) return null;

  if (loading && !dashboardData) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
        <span className="ml-2 text-gray-600">Loading your personalized dashboard...</span>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <AlertTriangle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No dashboard data available</p>
        </div>
      </div>
    );
  }

  const isAdmin = user.role === 'admin';
  const isManager = user.role === 'manager';
  const isEmployee = user.role === 'employee';
  const isAnalyst = user.role === 'analyst';

  const visibleAlerts = dashboardData.alerts?.filter(
    alert => !dismissedAlerts.includes(alert.id)
  ) || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        {/* <div>
          <h1 className="text-3xl font-bold text-slate-900">{dashboardData.greeting || 'Dashboard'}</h1>
          <p className="text-slate-600 mt-1">{dashboardData.date_range}</p>
        </div> */}
        <div className="flex items-center gap-3">
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value)}
            className="px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="day">Today</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
            <option value="quarter">This Quarter</option>
          </select>

          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 flex items-center gap-2 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Alerts */}
      {visibleAlerts.length > 0 && (
        <div className="space-y-2">
          {visibleAlerts.map((alert) => (
            <Alert 
              key={alert.id} 
              alert={alert} 
              onDismiss={handleDismissAlert}
            />
          ))}
        </div>
      )}

      {/* Welcome Stats */}
      {dashboardData.welcome_stats && (
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl p-6 text-white">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-indigo-100 text-sm">Total Employees</p>
              <p className="text-2xl font-bold">{dashboardData.welcome_stats.total_employees}</p>
            </div>
            <div>
              <p className="text-indigo-100 text-sm">Active Today</p>
              <p className="text-2xl font-bold">{dashboardData.welcome_stats.active_employees}</p>
            </div>
            <div>
              <p className="text-indigo-100 text-sm">Departments</p>
              <p className="text-2xl font-bold">{dashboardData.welcome_stats.departments || 0}</p>
            </div>
            <div>
              <p className="text-indigo-100 text-sm">Active Rate</p>
              <p className="text-2xl font-bold">{dashboardData.welcome_stats.active_percentage || 0}%</p>
            </div>
          </div>
        </div>
      )}

      {/* Personal Welcome for Employees */}
      {isEmployee && dashboardData.personal_welcome && (
        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">{dashboardData.greeting}</h2>
              <p className="text-indigo-100 mt-1">
                {dashboardData.personal_welcome.department} • Day off: {dashboardData.personal_welcome.day_off}
              </p>
            </div>
            <div className="text-right">
              <p className="text-indigo-100 text-sm">Your Status</p>
              <p className="text-xl font-semibold capitalize">{dashboardData.personal_welcome.status}</p>
            </div>
          </div>
        </div>
      )}

      {/* KPI Cards */}
      {dashboardData.quick_stats && dashboardData.quick_stats.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-6">
          {dashboardData.quick_stats.map((stat) => (
            <StatCard key={stat.id} stat={stat} />
          ))}
        </div>
      )}

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Productivity/Performance Trend */}
        {(dashboardData.productivity_trend_data || dashboardData.my_performance_data || dashboardData.team_productivity_data) && (
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <ChartInfo 
              title={dashboardData.productivity_trend?.title || 'Performance Trend'}
              description={dashboardData.productivity_trend?.description || 'Track your performance over time'}
              insights={dashboardData.productivity_chart_metadata?.key_insights}
            />
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={
                dashboardData.productivity_trend_data || 
                dashboardData.my_performance_data || 
                dashboardData.team_productivity_data || 
                []
              }>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="label" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip content={<CustomTooltip />} />
                <Area 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#6366f1" 
                  fillOpacity={1} 
                  fill="url(#colorValue)"
                  name="Performance %"
                  unit="%"
                />
              </AreaChart>
            </ResponsiveContainer>
            <p className="text-xs text-slate-500 mt-2">
              Source: Task completion data • Updated real-time
            </p>
          </div>
        )}

        {/* Task Status Distribution or Department Distribution */}
        {(dashboardData.task_status_data || dashboardData.department_distribution_data || dashboardData.my_task_data) && (
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <ChartInfo 
              title={dashboardData.task_status_distribution?.title || 'Task Distribution'}
              description={dashboardData.task_status_distribution?.description || 'Breakdown of tasks by status'}
              insights={dashboardData.task_chart_metadata?.key_insights}
            />
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={
                    dashboardData.task_status_data || 
                    dashboardData.department_distribution_data || 
                    dashboardData.my_task_data || 
                    []
                  }
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ label, value }) => `${label}: ${value}`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {(dashboardData.task_status_data || dashboardData.department_distribution_data || dashboardData.my_task_data || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color || COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex flex-wrap gap-3 mt-4">
              {(dashboardData.task_status_data || dashboardData.department_distribution_data || dashboardData.my_task_data || []).map((item, i) => (
                <div key={i} className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color || COLORS[i % COLORS.length] }} />
                  <span className="text-xs text-slate-600">{item.label}: {item.value}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Team Rankings for Manager */}
      {isManager && dashboardData.team_rankings_data && dashboardData.team_rankings_data.length > 0 && (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <ChartInfo 
            title={dashboardData.team_rankings?.title || 'Team Performance Rankings'}
            description={dashboardData.team_rankings?.description || 'Individual team member performance scores'}
            insights={dashboardData.team_rankings_metadata?.key_insights}
          />
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50">
                <tr>
                  <th className="text-left p-3 text-sm font-semibold text-slate-700">Rank</th>
                  <th className="text-left p-3 text-sm font-semibold text-slate-700">Team Member</th>
                  <th className="text-left p-3 text-sm font-semibold text-slate-700">Email</th>
                  <th className="text-center p-3 text-sm font-semibold text-slate-700">Tasks</th>
                  <th className="text-center p-3 text-sm font-semibold text-slate-700">Performance</th>
                  <th className="text-center p-3 text-sm font-semibold text-slate-700">Status</th>
                </tr>
              </thead>
              <tbody>
                {dashboardData.team_rankings_data.map((member) => (
                  <tr key={member.rank} className="border-t border-slate-100">
                    <td className="p-3 text-sm font-medium text-slate-700">#{member.rank}</td>
                    <td className="p-3">
                      <div className="text-sm font-medium text-slate-900">{member.name}</div>
                    </td>
                    <td className="p-3 text-sm text-slate-600">{member.email}</td>
                    <td className="p-3 text-center text-sm text-slate-900">{member.tasks}</td>
                    <td className="p-3 text-center">
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                        member.score >= 80 ? 'bg-green-100 text-green-800' :
                        member.score >= 60 ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {member.score}%
                      </span>
                    </td>
                    <td className="p-3 text-center">
                      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${
                        member.status === 'high' ? 'bg-emerald-100 text-emerald-800' :
                        member.status === 'medium' ? 'bg-amber-100 text-amber-800' :
                        'bg-rose-100 text-rose-800'
                      }`}>
                        {member.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Department Overview for Admin/Analyst */}
      {dashboardData.department_summaries && dashboardData.department_summaries.length > 0 && (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Department Performance Overview</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {dashboardData.department_summaries.map((dept) => (
              <DepartmentCard key={dept.id} dept={dept} />
            ))}
          </div>
        </div>
      )}

      {/* Top Performers for Admin */}
      {dashboardData.top_performers && dashboardData.top_performers.length > 0 && (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <ChartInfo 
            title={dashboardData.top_performers_metadata?.title || 'Top Performers'}
            description={dashboardData.top_performers_metadata?.description || 'Employees with highest performance scores'}
            insights={[dashboardData.top_performers_metadata?.criteria || 'Based on 80%+ completion rate']}
          />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {dashboardData.top_performers.slice(0, 6).map((performer) => (
              <div key={performer.rank} className="flex items-center gap-4 p-4 bg-slate-50 rounded-lg border border-slate-200">
                <div className="text-3xl">{performer.badge || '🏅'}</div>
                <div className="flex-1">
                  <div className="font-medium text-slate-900">{performer.name}</div>
                  <div className="text-xs text-slate-500">{performer.department}</div>
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-slate-600">Score</span>
                    <span className="text-sm font-semibold text-indigo-600">{performer.score}%</span>
                  </div>
                  <div className="w-full h-1.5 bg-slate-200 rounded-full mt-1">
                    <div 
                      className="h-full bg-indigo-500 rounded-full"
                      style={{ width: `${performer.score}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Active and Upcoming Tasks */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Active Tasks */}
        {dashboardData.active_tasks && dashboardData.active_tasks.length > 0 && (
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Active Tasks</h3>
            <div className="space-y-3">
              {dashboardData.active_tasks.map((task) => (
                <TaskItem key={task.id} task={task} />
              ))}
            </div>
          </div>
        )}

        {/* Upcoming Tasks */}
        {dashboardData.upcoming_tasks && dashboardData.upcoming_tasks.length > 0 && (
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Upcoming Tasks</h3>
            <div className="space-y-3">
              {dashboardData.upcoming_tasks.map((task) => (
                <TaskItem key={task.id} task={task} />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Today's Schedule for Employee */}
      {isEmployee && dashboardData.today_schedule && dashboardData.today_schedule.length > 0 && (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Today's Schedule</h3>
          <div className="space-y-3">
            {dashboardData.today_schedule.map((item, index) => (
              <div key={index} className="flex items-center gap-4 p-3 bg-slate-50 rounded-lg">
                <div className="w-16 text-sm font-medium text-slate-700">{item.time}</div>
                <div className="flex-1">
                  <div className="font-medium text-slate-900">{item.task}</div>
                  <div className="flex items-center gap-2 mt-1">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      item.priority === 'high' ? 'bg-red-100 text-red-800' :
                      item.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                      'bg-green-100 text-green-800'
                    }`}>
                      {item.priority}
                    </span>
                    <span className="text-xs text-slate-500 capitalize">{item.status}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Insights and Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Insights */}
        {dashboardData.insights && dashboardData.insights.length > 0 && (
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Key Insights</h3>
            <div className="space-y-3">
              {dashboardData.insights.map((insight, index) => (
                <InsightCard key={index} insight={insight} />
              ))}
            </div>
          </div>
        )}

        {/* Recommendations */}
        {dashboardData.recommendations && dashboardData.recommendations.length > 0 && (
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Recommendations</h3>
            <div className="space-y-3">
              {dashboardData.recommendations.map((rec, index) => (
                <div key={index} className="p-4 bg-indigo-50 rounded-lg border border-indigo-200">
                  <h4 className="font-medium text-indigo-900 mb-1">{rec.title}</h4>
                  <p className="text-sm text-indigo-700 mb-3">{rec.description}</p>
                 
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Achievements for Employee */}
      {isEmployee && dashboardData.achievements && dashboardData.achievements.length > 0 && (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Your Achievements</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {dashboardData.achievements.map((achievement, index) => (
              <AchievementCard key={index} achievement={achievement} />
            ))}
          </div>
        </div>
      )}

      {/* Recent Activity */}
      {dashboardData.recent_activities && dashboardData.recent_activities.length > 0 && (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">Recent Activity</h3>
          <div className="space-y-1">
            {dashboardData.recent_activities.map((activity) => (
              <ActivityItem key={activity.id} activity={activity} />
            ))}
          </div>
        </div>
      )}

      {/* System Health for Admin */}
      {isAdmin && dashboardData.system_health && (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">System Health</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 bg-slate-50 rounded-lg">
              <p className="text-sm text-slate-600">Status</p>
              <p className="text-lg font-semibold text-emerald-600 capitalize">{dashboardData.system_health.status}</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-lg">
              <p className="text-sm text-slate-600">Uptime</p>
              <p className="text-lg font-semibold text-slate-900">{dashboardData.system_health.uptime}</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-lg">
              <p className="text-sm text-slate-600">Response Time</p>
              <p className="text-lg font-semibold text-slate-900">{dashboardData.system_health.response_time}</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-lg">
              <p className="text-sm text-slate-600">Active Sessions</p>
              <p className="text-lg font-semibold text-slate-900">{dashboardData.system_health.active_sessions}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}