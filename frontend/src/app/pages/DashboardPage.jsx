import React from 'react';
import { useAuth } from './app/contexts/AuthContext';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, Activity, Users, Target, CheckCircle, AlertTriangle, Award } from 'lucide-react';
import { getChartData, getDepartmentData, mockPerformanceData } from './app/utils/mockData';

export const DashboardPage = () => {
  const { user } = useAuth();
  const chartData = getChartData();
  const departmentData = getDepartmentData();

  const isAdmin = user?.role === 'admin';
  const isManager = user?.role === 'manager';
  const isAnalyst = user?.role === 'data-analyst';
  const isEmployee = user?.role === 'employee';

  // Filter data based on role
  const performanceData = isEmployee 
    ? mockPerformanceData.filter(p => p.employeeName === user?.name)
    : mockPerformanceData;

  const COLORS = ['#0ea5e9', '#6366f1', '#8b5cf6', '#ec4899', '#f59e0b'];

  // Calculate stats
  const avgProductivity = Math.round(performanceData.reduce((acc, p) => acc + p.productivityScore, 0) / performanceData.length);
  const avgAttendance = Math.round(performanceData.reduce((acc, p) => acc + p.attendanceRate, 0) / performanceData.length);
  const avgCompletion = Math.round(performanceData.reduce((acc, p) => acc + p.taskCompletionRate, 0) / performanceData.length);

  const stats = [
    { 
      title: 'Average Productivity', 
      value: `${avgProductivity}%`, 
      change: '+5.2%',
      trend: 'up',
      icon: Activity,
      color: 'text-sky-600',
      bgColor: 'bg-sky-50'
    },
    { 
      title: 'Attendance Rate', 
      value: `${avgAttendance}%`, 
      change: '+2.1%',
      trend: 'up',
      icon: CheckCircle,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50'
    },
    { 
      title: 'Task Completion', 
      value: `${avgCompletion}%`, 
      change: '+3.4%',
      trend: 'up',
      icon: Target,
      color: 'text-cyan-600',
      bgColor: 'bg-cyan-50'
    },
    { 
      title: isEmployee ? 'My Performance' : 'Team Members', 
      value: isEmployee ? 'Good' : performanceData.length.toString(), 
      change: isEmployee ? 'Top 25%' : '+2 this month',
      trend: 'up',
      icon: isEmployee ? Award : Users,
      color: 'text-slate-600',
      bgColor: 'bg-slate-50'
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl text-slate-900">
            {isEmployee ? 'My Dashboard' : 'Dashboard'}
          </h1>
          <p className="text-slate-600 mt-1">
            Welcome back, {user?.name}! Here's your performance overview.
          </p>
        </div>
        <div className="text-right">
          <div className="text-sm text-slate-500">Last Updated</div>
          <div className="text-slate-900">Today, 10:30 AM</div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="bg-white p-6 rounded-lg border border-slate-200">
              <div className="flex flex-row items-center justify-between pb-4">
                <h3 className="text-sm text-slate-600 font-medium">{stat.title}</h3>
                <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                  <Icon className={`h-5 w-5 ${stat.color}`} />
                </div>
              </div>
              <div>
                <div className="text-3xl text-slate-900">{stat.value}</div>
                <div className="flex items-center gap-1 mt-1">
                  {stat.trend === 'up' ? (
                    <TrendingUp className="h-4 w-4 text-green-600" />
                  ) : (
                    <TrendingDown className="h-4 w-4 text-red-600" />
                  )}
                  <span className={`text-sm ${stat.trend === 'up' ? 'text-green-600' : 'text-red-600'}`}>
                    {stat.change}
                  </span>
                  <span className="text-sm text-slate-500 ml-1">from last month</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance Trends */}
        <div className="bg-white p-6 rounded-lg border border-slate-200">
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-slate-900">Performance Trends</h3>
            <p className="text-slate-600 mt-1">
              Monthly performance metrics over time
            </p>
          </div>
          <div>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="month" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }}
                />
                <Legend />
                <Line type="monotone" dataKey="productivity" stroke="#0ea5e9" strokeWidth={2} name="Productivity" />
                <Line type="monotone" dataKey="attendance" stroke="#6366f1" strokeWidth={2} name="Attendance" />
                <Line type="monotone" dataKey="completion" stroke="#8b5cf6" strokeWidth={2} name="Task Completion" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Department Performance */}
        {(isAdmin || isManager || isAnalyst) && (
          <div className="bg-white p-6 rounded-lg border border-slate-200">
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-slate-900">Department Overview</h3>
              <p className="text-slate-600 mt-1">
                Performance by department
              </p>
            </div>
            <div>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={departmentData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="department" stroke="#64748b" />
                  <YAxis stroke="#64748b" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#fff', border: '1px solid #e2e8f0', borderRadius: '8px' }}
                  />
                  <Legend />
                  <Bar dataKey="avgScore" fill="#0ea5e9" name="Avg Score" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Employee Score Distribution (for employee view) */}
        {isEmployee && (
          <div className="bg-white p-6 rounded-lg border border-slate-200">
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-slate-900">My Performance Breakdown</h3>
              <p className="text-slate-600 mt-1">
                Score distribution across metrics
              </p>
            </div>
            <div>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Productivity', value: avgProductivity },
                      { name: 'Attendance', value: avgAttendance },
                      { name: 'Task Completion', value: avgCompletion },
                    ]}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {COLORS.map((color, index) => (
                      <Cell key={`cell-${index}`} fill={color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      {/* Recent Performance Table */}
      <div className="bg-white p-6 rounded-lg border border-slate-200">
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-slate-900">
            {isEmployee ? 'My Recent Performance' : 'Team Performance'}
          </h3>
          <p className="text-slate-600 mt-1">
            Latest performance metrics and trends
          </p>
        </div>
        <div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-3 px-4 text-sm text-slate-600">Employee</th>
                  <th className="text-left py-3 px-4 text-sm text-slate-600">Department</th>
                  <th className="text-right py-3 px-4 text-sm text-slate-600">Productivity</th>
                  <th className="text-right py-3 px-4 text-sm text-slate-600">Attendance</th>
                  <th className="text-right py-3 px-4 text-sm text-slate-600">Tasks</th>
                  <th className="text-center py-3 px-4 text-sm text-slate-600">Trend</th>
                </tr>
              </thead>
              <tbody>
                {performanceData.slice(0, 5).map((item) => (
                  <tr key={item.id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="py-3 px-4">
                      <div className="text-sm text-slate-900">{item.employeeName}</div>
                      <div className="text-xs text-slate-500">{item.employeeId}</div>
                    </td>
                    <td className="py-3 px-4 text-sm text-slate-600">{item.department}</td>
                    <td className="py-3 px-4 text-right">
                      <span className={`text-sm ${item.productivityScore >= 90 ? 'text-green-600' : item.productivityScore >= 70 ? 'text-slate-900' : 'text-red-600'}`}>
                        {item.productivityScore}%
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right text-sm text-slate-900">{item.attendanceRate}%</td>
                    <td className="py-3 px-4 text-right text-sm text-slate-900">{item.taskCompletionRate}%</td>
                    <td className="py-3 px-4 text-center">
                      {item.trend === 'up' ? (
                        <TrendingUp className="h-5 w-5 text-green-600 mx-auto" />
                      ) : item.trend === 'down' ? (
                        <TrendingDown className="h-5 w-5 text-red-600 mx-auto" />
                      ) : (
                        <AlertTriangle className="h-5 w-5 text-yellow-600 mx-auto" />
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};