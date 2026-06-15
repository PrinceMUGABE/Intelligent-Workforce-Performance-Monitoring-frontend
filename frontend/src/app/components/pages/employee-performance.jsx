/* eslint-disable no-unused-vars */
import { useState } from 'react';
import { mockPerformanceData, mockTaskAssignments } from '../../utils/mockData';
import { TrendingUp, TrendingDown, Minus, Target, Award, CheckCircle2, AlertCircle, Calendar } from 'lucide-react';
import { useAuth } from '../../context/auth-context';

export default function EmployeePerformance() {
  const { user } = useAuth();
  
  if (!user) return null;

  // Get only the logged-in employee's performance data
  const myPerformance = mockPerformanceData.find(p => p.employeeId === user.id);
  
  // Get the employee's task assignments
  const myAssignments = mockTaskAssignments.filter(a => a.employeeId === user.id);
  
  // Calculate active and completed tasks
  const activeTasks = myAssignments.filter(a => a.status === 'assigned' || a.status === 'in_progress');
  const completedTasks = myAssignments.filter(a => a.status === 'completed');
  const overdueTasks = myAssignments.filter(a => a.status === 'overdue');

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'up': return <TrendingUp className="w-4 h-4 text-green-600" />;
      case 'down': return <TrendingDown className="w-4 h-4 text-red-600" />;
      default: return <Minus className="w-4 h-4 text-slate-600" />;
    }
  };

  const getPerformanceColor = (score) => {
    if (score >= 90) return 'bg-green-100 text-green-700';
    if (score >= 80) return 'bg-blue-100 text-blue-700';
    if (score >= 70) return 'bg-yellow-100 text-yellow-700';
    return 'bg-red-100 text-red-700';
  };

  const getPerformanceLabel = (score) => {
    if (score >= 90) return 'Excellent';
    if (score >= 80) return 'Good';
    if (score >= 70) return 'Average';
    return 'Needs Improvement';
  };

  if (!myPerformance) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl text-slate-900">My Performance</h1>
          <p className="text-slate-600 mt-1">View your personal performance metrics and task completion data</p>
        </div>
        <div className="bg-white p-6 rounded-lg border border-slate-200">
          <div className="py-12 text-center">
            <AlertCircle className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <p className="text-slate-600">No performance data available yet.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl text-slate-900">My Performance</h1>
        <p className="text-slate-600 mt-1">View your personal performance metrics and task completion data</p>
      </div>

      {/* Summary Cards */}
      <div className="grid md:grid-cols-4 gap-4">
        <div className="bg-blue-50 p-6 rounded-lg border border-blue-200">
          <div className="pb-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm text-blue-700 font-medium">Productivity Score</h3>
              <Target className="w-5 h-5 text-blue-600" />
            </div>
          </div>
          <div>
            <div className="text-3xl text-blue-900 font-semibold">{myPerformance.productivityScore}%</div>
            <div className="flex items-center gap-1 mt-1">
              {getTrendIcon(myPerformance.trend)}
              <span className={`text-xs ${myPerformance.trend === 'up' ? 'text-green-600' : myPerformance.trend === 'down' ? 'text-red-600' : 'text-slate-600'}`}>
                {myPerformance.trend === 'up' ? 'Improving' : myPerformance.trend === 'down' ? 'Declining' : 'Stable'}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-green-50 p-6 rounded-lg border border-green-200">
          <div className="pb-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm text-green-700 font-medium">Task Completion</h3>
              <CheckCircle2 className="w-5 h-5 text-green-600" />
            </div>
          </div>
          <div>
            <div className="text-3xl text-green-900 font-semibold">{myPerformance.taskCompletionRate}%</div>
            <p className="text-xs text-green-700 mt-1">{myPerformance.completedTasks} of {myPerformance.totalTasks} tasks</p>
          </div>
        </div>

        <div className="bg-purple-50 p-6 rounded-lg border border-purple-200">
          <div className="pb-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm text-purple-700 font-medium">Attendance Rate</h3>
              <Calendar className="w-5 h-5 text-purple-600" />
            </div>
          </div>
          <div>
            <div className="text-3xl text-purple-900 font-semibold">{myPerformance.attendanceRate}%</div>
            <p className="text-xs text-purple-700 mt-1">Based on average task progress</p>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border border-slate-200">
          <div className="pb-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm text-slate-600 font-medium">Performance Level</h3>
              <Award className="w-5 h-5 text-slate-400" />
            </div>
          </div>
          <div>
            <span className={`px-3 py-1 rounded-full text-sm ${getPerformanceColor(myPerformance.productivityScore)}`}>
              {getPerformanceLabel(myPerformance.productivityScore)}
            </span>
            <p className="text-xs text-slate-500 mt-2">Period: {myPerformance.period}</p>
          </div>
        </div>
      </div>

      {/* Performance Details Card */}
      <div className="bg-white p-6 rounded-lg border border-slate-200">
        <div className="mb-6">
          <h3 className="text-xl font-semibold text-slate-900">Performance Breakdown</h3>
        </div>
        <div className="space-y-6">
          {/* Productivity Score */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-slate-700">Productivity Score</span>
              <span className="text-sm font-semibold text-slate-900">{myPerformance.productivityScore}%</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-3">
              <div 
                className={`h-3 rounded-full transition-all ${
                  myPerformance.productivityScore >= 90 ? 'bg-green-500' :
                  myPerformance.productivityScore >= 80 ? 'bg-blue-500' :
                  myPerformance.productivityScore >= 70 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${myPerformance.productivityScore}%` }}
              />
            </div>
            <p className="text-xs text-slate-500 mt-1">Based on average task progress</p>
          </div>

          {/* Task Completion Rate */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-slate-700">Task Completion Rate</span>
              <span className="text-sm font-semibold text-slate-900">{myPerformance.taskCompletionRate}%</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-3">
              <div 
                className={`h-3 rounded-full transition-all ${
                  myPerformance.taskCompletionRate >= 90 ? 'bg-green-500' :
                  myPerformance.taskCompletionRate >= 80 ? 'bg-blue-500' :
                  myPerformance.taskCompletionRate >= 70 ? 'bg-yellow-500' : 'bg-red-500'
                }`}
                style={{ width: `${myPerformance.taskCompletionRate}%` }}
              />
            </div>
            <p className="text-xs text-slate-500 mt-1">{myPerformance.completedTasks} of {myPerformance.totalTasks} tasks completed</p>
          </div>

          {/* Attendance Rate */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-medium text-slate-700">Attendance Rate</span>
              <span className="text-sm font-semibold text-slate-900">{myPerformance.attendanceRate}%</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-3">
              <div 
                className="h-3 rounded-full transition-all bg-purple-500"
                style={{ width: `${myPerformance.attendanceRate}%` }}
              />
            </div>
            <p className="text-xs text-slate-500 mt-1">Calculated from task activity</p>
          </div>
        </div>
      </div>

      {/* Active Tasks Overview */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg border border-slate-200">
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-slate-900">Current Tasks</h3>
          </div>
          <div className="space-y-3">
            {activeTasks.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-4">No active tasks</p>
            ) : (
              activeTasks.map((assignment) => (
                <div key={assignment.id} className="p-3 bg-slate-50 rounded-lg">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="text-sm font-medium text-slate-900">{assignment.taskTitle}</h4>
                    <span 
                      className={`text-xs px-2 py-1 rounded-full border ${
                        assignment.status === 'in_progress' ? 'border-blue-300 text-blue-700 bg-blue-50' :
                        'border-slate-300 text-slate-700 bg-slate-50'
                      }`}
                    >
                      {assignment.status === 'in_progress' ? 'In Progress' : 'Assigned'}
                    </span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-xs text-slate-600">
                      <span>Progress</span>
                      <span className="font-medium">{assignment.progress}%</span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2">
                      <div 
                        className="h-2 rounded-full bg-blue-500 transition-all"
                        style={{ width: `${assignment.progress}%` }}
                      />
                    </div>
                    <p className="text-xs text-slate-500">
                      Days to complete: {assignment.daysToComplete}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg border border-slate-200">
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-slate-900">Task Statistics</h3>
          </div>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
                <span className="text-sm text-slate-700">Completed Tasks</span>
              </div>
              <span className="text-lg font-semibold text-green-700">{completedTasks.length}</span>
            </div>

            <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-blue-600" />
                <span className="text-sm text-slate-700">Active Tasks</span>
              </div>
              <span className="text-lg font-semibold text-blue-700">{activeTasks.length}</span>
            </div>

            {overdueTasks.length > 0 && (
              <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-red-600" />
                  <span className="text-sm text-slate-700">Overdue Tasks</span>
                </div>
                <span className="text-lg font-semibold text-red-700">{overdueTasks.length}</span>
              </div>
            )}

            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
              <div className="flex items-center gap-2">
                <Target className="w-5 h-5 text-slate-600" />
                <span className="text-sm text-slate-700">Total Assigned</span>
              </div>
              <span className="text-lg font-semibold text-slate-700">{myAssignments.length}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}