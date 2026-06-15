/* eslint-disable react-hooks/exhaustive-deps */
import { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { TrendingUp, Users, Award, Calendar, Loader2, RefreshCw, AlertCircle, CheckCircle, XCircle, Clock, TrendingDown, ArrowUp, ArrowDown } from 'lucide-react';
import { useAuth } from '../../context/auth-context';
import { toast } from 'sonner';
import { UserCheck } from 'lucide-react';

const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6'];

export default function Analytics() {
  const { user, api } = useAuth();
  const [timeRange, setTimeRange] = useState('6months');
  const [department, setDepartment] = useState('all');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [analyticsData, setAnalyticsData] = useState(null);
  const [departments, setDepartments] = useState([]);

  // Fetch departments for filter
  useEffect(() => {
    fetchDepartments();
  }, []);

  // Fetch analytics data
  useEffect(() => {
    if (user) {
      fetchAnalyticsData();
    }
  }, [user, timeRange, department]);

  const fetchDepartments = async () => {
    try {
      const response = await api.get('http://127.0.0.1:8000/departments/all/');
      setDepartments(response.data.departments || []);
    } catch (error) {
      console.error('Error fetching departments:', error);
    }
  };

  const fetchAnalyticsData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('time_range', timeRange);
      if (department !== 'all') {
        params.append('department_id', department);
      }

      const response = await api.get(`http://127.0.0.1:8000/analytics/dashboard/?${params}`);
      setAnalyticsData(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
      toast.error('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAnalyticsData();
    setRefreshing(false);
    toast.success('Analytics data refreshed');
  };

  // Get role-specific description
  const getDescription = () => {
    if (user?.role === 'admin') return 'Comprehensive analytics dashboard with system-wide performance trends and insights';
    if (user?.role === 'manager') return 'Team performance analytics, trends, and productivity insights for your department';
    if (user?.role === 'analyst') return 'Advanced workforce data analytics with detailed metrics and statistical insights';
    return 'Workforce performance insights and trends';
  };

  if (loading && !analyticsData) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
        <span className="ml-2 text-gray-600">Loading analytics...</span>
      </div>
    );
  }

  if (!analyticsData) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No analytics data available</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Analytics</h1>
          <p className="text-slate-600 mt-1">{getDescription()}</p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 flex items-center gap-2 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>

          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
          >
            <option value="1month">Last Month</option>
            <option value="3months">Last 3 Months</option>
            <option value="6months">Last 6 Months</option>
            <option value="1year">Last Year</option>
          </select>

          {user?.role !== 'employee' && departments.length > 0 && (
            <select
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
            >
              <option value="all">All Departments</option>
              {departments.map(dept => (
                <option key={dept.id} value={dept.id}>
                  {dept.name}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
        <MetricCard
          title="Avg Performance"
          value={`${analyticsData.avg_performance?.value?.toFixed(1) || 0}%`}
          trend={analyticsData.avg_performance?.trend || 0}
          icon={<TrendingUp className="w-5 h-5" />}
          color="indigo"
        />
        <MetricCard
          title="Total Employees"
          value={analyticsData.total_employees?.value || 0}
          trend={analyticsData.total_employees?.trend || 0}
          icon={<Users className="w-5 h-5" />}
          color="violet"
        />
        <MetricCard
          title="Active Employees"
          value={analyticsData.active_employees?.value || 0}
          trend={analyticsData.active_employees?.trend || 0}
          icon={<UserCheck className="w-5 h-5" />}
          color="emerald"
        />
        <MetricCard
          title="Top Performers"
          value={analyticsData.top_performers?.value || 0}
          trend={analyticsData.top_performers?.trend || 0}
          icon={<Award className="w-5 h-5" />}
          color="sky"
        />
        <MetricCard
          title="Completion Rate"
          value={`${analyticsData.task_completion_rate?.value?.toFixed(1) || 0}%`}
          trend={analyticsData.task_completion_rate?.trend || 0}
          icon={<CheckCircle className="w-5 h-5" />}
          color="amber"
        />
      </div>

      {/* Performance Trends */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <h2 className="text-lg font-semibold text-slate-900 mb-4">Performance Trends</h2>
        <ResponsiveContainer width="100%" height={350}>
          <AreaChart data={analyticsData.monthly_trends || []}>
            <defs>
              <linearGradient id="colorProductivity" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorAttendance" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
            <XAxis dataKey="month" stroke="#64748b" />
            <YAxis stroke="#64748b" />
            <Tooltip />
            <Legend />
            <Area type="monotone" dataKey="productivity" stroke="#6366f1" fillOpacity={1} fill="url(#colorProductivity)" name="Productivity" />
            <Area type="monotone" dataKey="attendance" stroke="#8b5cf6" fillOpacity={1} fill="url(#colorAttendance)" name="Attendance" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Department Performance */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Department Performance</h2>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={analyticsData.department_performance || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="department" stroke="#64748b" />
              <YAxis stroke="#64748b" />
              <Tooltip />
              <Legend />
              <Bar dataKey="performance" fill="#6366f1" radius={[8, 8, 0, 0]} name="Performance %" />
              <Bar dataKey="employees" fill="#8b5cf6" radius={[8, 8, 0, 0]} name="Employees" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Task Status Distribution */}
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Task Status Distribution</h2>
          <ResponsiveContainer width="100%" height={350}>
            <PieChart>
              <Pie
                data={analyticsData.task_status_distribution || []}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ status, percentage }) => `${status}: ${percentage}%`}
                outerRadius={120}
                fill="#8884d8"
                dataKey="count"
                nameKey="status"
              >
                {(analyticsData.task_status_distribution || []).map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Day-Off Analytics */}
      {analyticsData.dayoff_analytics && (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Day-Off Request Analytics</h2>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
            <div className="text-center">
              <div className="text-2xl font-bold text-slate-900">
                {analyticsData.dayoff_analytics.total_requests}
              </div>
              <div className="text-sm text-slate-600">Total Requests</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-yellow-600">
                {analyticsData.dayoff_analytics.pending_requests}
              </div>
              <div className="text-sm text-slate-600">Pending</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {analyticsData.dayoff_analytics.approved_requests}
              </div>
              <div className="text-sm text-slate-600">Approved</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">
                {analyticsData.dayoff_analytics.rejected_requests}
              </div>
              <div className="text-sm text-slate-600">Rejected</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-slate-600">
                {analyticsData.dayoff_analytics.approval_rate?.toFixed(1)}%
              </div>
              <div className="text-sm text-slate-600">Approval Rate</div>
            </div>
          </div>

          {/* Day-off by day distribution */}
          {Object.keys(analyticsData.dayoff_analytics.by_day || {}).length > 0 && (
            <div className="mt-4">
              <h3 className="text-sm font-medium text-slate-700 mb-3">Requests by Day</h3>
              <div className="grid grid-cols-7 gap-2">
                {Object.entries(analyticsData.dayoff_analytics.by_day).map(([day, count]) => (
                  <div key={day} className="bg-slate-50 p-3 rounded-lg text-center">
                    <div className="text-xs text-slate-600 capitalize mb-1">{day}</div>
                    <div className="text-lg font-semibold text-slate-900">{count}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Top Performers */}
      {analyticsData.top_performers_list && analyticsData.top_performers_list.length > 0 && (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Top Performers</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50">
                <tr>
                  <th className="text-left p-3 text-sm font-semibold text-slate-700">Employee</th>
                  <th className="text-left p-3 text-sm font-semibold text-slate-700">Department</th>
                  <th className="text-center p-3 text-sm font-semibold text-slate-700">Completed</th>
                  <th className="text-center p-3 text-sm font-semibold text-slate-700">Active</th>
                  <th className="text-center p-3 text-sm font-semibold text-slate-700">Completion Rate</th>
                  <th className="text-center p-3 text-sm font-semibold text-slate-700">Performance Score</th>
                </tr>
              </thead>
              <tbody>
                {analyticsData.top_performers_list.map((performer, index) => (
                  <tr key={performer.user_id} className="border-t border-slate-100">
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                          index === 0 ? 'bg-yellow-100 text-yellow-600' :
                          index === 1 ? 'bg-slate-100 text-slate-600' :
                          index === 2 ? 'bg-orange-100 text-orange-600' :
                          'bg-indigo-100 text-indigo-600'
                        }`}>
                          {index + 1}
                        </div>
                        <div>
                          <div className="text-sm font-medium text-slate-900">{performer.full_name}</div>
                          <div className="text-xs text-slate-500">{performer.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="p-3 text-sm text-slate-600">{performer.department}</td>
                    <td className="p-3 text-center text-sm text-slate-900">{performer.tasks_completed}</td>
                    <td className="p-3 text-center text-sm text-slate-900">{performer.tasks_active}</td>
                    <td className="p-3 text-center">
                      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        {performer.completion_rate?.toFixed(1)}%
                      </span>
                    </td>
                    <td className="p-3 text-center">
                      <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                        {performer.performance_score?.toFixed(1)}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Insights */}
      {analyticsData.insights && analyticsData.insights.length > 0 && (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Key Insights & Recommendations</h2>
          <div className="space-y-3">
            {analyticsData.insights.map((insight, index) => (
              <InsightCard
                key={index}
                type={insight.type}
                title={insight.title}
                description={insight.description}
                priority={insight.priority}
              />
            ))}
          </div>
        </div>
      )}

      {/* Metadata */}
      <div className="text-center text-sm text-slate-500">
        <p>
          Analytics generated for period: {new Date(analyticsData.period_start).toLocaleDateString()} - {new Date(analyticsData.period_end).toLocaleDateString()}
        </p>
        <p className="mt-1">
          Last updated: {new Date(analyticsData.generated_at).toLocaleString()}
        </p>
      </div>
    </div>
  );
}

function MetricCard({ title, value, trend, icon, color }) {
  const colors = {
    indigo: 'bg-indigo-100 text-indigo-600',
    violet: 'bg-violet-100 text-violet-600',
    sky: 'bg-sky-100 text-sky-600',
    emerald: 'bg-emerald-100 text-emerald-600',
    amber: 'bg-amber-100 text-amber-600',
  };

  const trendIcon = trend > 0 ? (
    <ArrowUp className="w-3 h-3" />
  ) : trend < 0 ? (
    <ArrowDown className="w-3 h-3" />
  ) : null;

  return (
    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${colors[color] || colors.indigo} mb-3`}>
        {icon}
      </div>
      <div className="text-2xl font-bold text-slate-900 mb-1">{value}</div>
      <div className="flex items-center justify-between">
        <div className="text-sm text-slate-600">{title}</div>
        {trend !== 0 && (
          <div className={`flex items-center gap-1 text-xs font-medium ${trend > 0 ? 'text-emerald-600' : 'text-red-600'}`}>
            {trendIcon}
            {Math.abs(trend).toFixed(1)}%
          </div>
        )}
      </div>
    </div>
  );
}

function InsightCard({ type, title, description, priority }) {
  const colors = {
    success: 'bg-emerald-50 border-emerald-200 text-emerald-800',
    warning: 'bg-amber-50 border-amber-200 text-amber-800',
    info: 'bg-sky-50 border-sky-200 text-sky-800',
    error: 'bg-red-50 border-red-200 text-red-800',
  };

  const icons = {
    success: <CheckCircle className="w-5 h-5" />,
    warning: <AlertCircle className="w-5 h-5" />,
    info: <Clock className="w-5 h-5" />,
    error: <XCircle className="w-5 h-5" />,
  };

  return (
    <div className={`p-4 rounded-lg border ${colors[type] || colors.info} flex items-start gap-3`}>
      <div className="flex-shrink-0 mt-0.5">
        {icons[type]}
      </div>
      <div className="flex-1">
        <div className="font-medium mb-1 flex items-center gap-2">
          {title}
          {priority === 'high' && (
            <span className="px-2 py-0.5 text-xs bg-red-100 text-red-700 rounded-full">High Priority</span>
          )}
        </div>
        <div className="text-sm opacity-90">{description}</div>
      </div>
    </div>
  );
}

