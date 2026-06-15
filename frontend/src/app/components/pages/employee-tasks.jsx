import { useState } from 'react';
import { mockTaskAssignments, mockTasks } from '../../utils/mockData';
import { Search, Calendar, Clock, CheckCircle2, Circle, AlertCircle, TrendingUp } from 'lucide-react';
import { useAuth } from '../../context/auth-context';

export default function EmployeeTasks() {
  const { user } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 6;

  if (!user) return null;

  // Get only the logged-in employee's task assignments
  const myAssignments = mockTaskAssignments.filter(a => a.employeeId === user.id);

  // Filter assignments
  const filteredAssignments = myAssignments.filter(assignment => {
    const matchesSearch = assignment.taskTitle.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || assignment.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  // Pagination
  const totalPages = Math.ceil(filteredAssignments.length / itemsPerPage);
  const paginatedAssignments = filteredAssignments.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // Calculate summary stats
  const totalAssigned = myAssignments.length;
  const completedCount = myAssignments.filter(a => a.status === 'completed').length;
  const inProgressCount = myAssignments.filter(a => a.status === 'in_progress').length;
  const overdueCount = myAssignments.filter(a => a.status === 'overdue').length;
  const completionRate = totalAssigned > 0 ? Math.round((completedCount / totalAssigned) * 100) : 0;

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-700 border-green-300';
      case 'in_progress': return 'bg-blue-100 text-blue-700 border-blue-300';
      case 'assigned': return 'bg-slate-100 text-slate-700 border-slate-300';
      case 'overdue': return 'bg-red-100 text-red-700 border-red-300';
      case 'cancelled': return 'bg-gray-100 text-gray-700 border-gray-300';
      default: return 'bg-slate-100 text-slate-700 border-slate-300';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle2 className="w-4 h-4" />;
      case 'in_progress': return <Clock className="w-4 h-4" />;
      case 'overdue': return <AlertCircle className="w-4 h-4" />;
      default: return <Circle className="w-4 h-4" />;
    }
  };

  const formatStatus = (status) => {
    return status.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl text-slate-900">My Assigned Tasks</h1>
        <p className="text-slate-600 mt-1">View and track your assigned tasks and their progress</p>
      </div>

      {/* Summary Cards */}
      <div className="grid md:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg border border-slate-200">
          <div className="pb-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm text-slate-600 font-medium">Total Assigned</h3>
              <Circle className="w-5 h-5 text-slate-400" />
            </div>
          </div>
          <div>
            <div className="text-3xl text-slate-900">{totalAssigned}</div>
            <p className="text-xs text-slate-500 mt-1">All tasks assigned to you</p>
          </div>
        </div>

        <div className="bg-blue-50 p-6 rounded-lg border border-blue-200">
          <div className="pb-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm text-blue-700 font-medium">In Progress</h3>
              <Clock className="w-5 h-5 text-blue-600" />
            </div>
          </div>
          <div>
            <div className="text-3xl text-blue-900">{inProgressCount}</div>
            <p className="text-xs text-blue-700 mt-1">Currently working on</p>
          </div>
        </div>

        <div className="bg-green-50 p-6 rounded-lg border border-green-200">
          <div className="pb-3">
            <div className="flex items-center justify-between">
              <h3 className="text-sm text-green-700 font-medium">Completed</h3>
              <CheckCircle2 className="w-5 h-5 text-green-600" />
            </div>
          </div>
          <div>
            <div className="text-3xl text-green-900">{completedCount}</div>
            <p className="text-xs text-green-700 mt-1">{completionRate}% completion rate</p>
          </div>
        </div>

        {overdueCount > 0 ? (
          <div className="bg-red-50 p-6 rounded-lg border border-red-200">
            <div className="pb-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm text-red-700 font-medium">Overdue</h3>
                <AlertCircle className="w-5 h-5 text-red-600" />
              </div>
            </div>
            <div>
              <div className="text-3xl text-red-900">{overdueCount}</div>
              <p className="text-xs text-red-700 mt-1">Needs immediate attention</p>
            </div>
          </div>
        ) : (
          <div className="bg-purple-50 p-6 rounded-lg border border-purple-200">
            <div className="pb-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm text-purple-700 font-medium">On Track</h3>
                <TrendingUp className="w-5 h-5 text-purple-600" />
              </div>
            </div>
            <div>
              <div className="text-3xl text-purple-900">100%</div>
              <p className="text-xs text-purple-700 mt-1">No overdue tasks</p>
            </div>
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="bg-white p-6 rounded-lg border border-slate-200">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search tasks..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setCurrentPage(1);
              }}
              className="w-full pl-10 p-2 border border-slate-300 rounded-lg"
            />
          </div>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="all">All Statuses</option>
            <option value="assigned">Assigned</option>
            <option value="in_progress">In Progress</option>
            <option value="completed">Completed</option>
            <option value="overdue">Overdue</option>
          </select>
        </div>
      </div>

      {/* Tasks List */}
      {paginatedAssignments.length === 0 ? (
        <div className="bg-white p-6 rounded-lg border border-slate-200">
          <div className="py-12 text-center">
            <Circle className="w-12 h-12 text-slate-400 mx-auto mb-4" />
            <p className="text-slate-600">No tasks found matching your filters.</p>
          </div>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-6">
          {paginatedAssignments.map((assignment) => {
            const task = mockTasks.find(t => t.id === assignment.taskId);
            const priorityColor = task?.priority === 'urgent' ? 'text-red-600' :
                                 task?.priority === 'high' ? 'text-orange-600' :
                                 task?.priority === 'medium' ? 'text-yellow-600' : 'text-slate-600';

            return (
              <div key={assignment.id} className="bg-white p-6 rounded-lg border border-slate-200 hover:shadow-md transition-shadow">
                <div className="mb-6">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <h3 className="text-lg font-semibold text-slate-900 mb-2">{assignment.taskTitle}</h3>
                      {task && (
                        <p className="text-sm text-slate-600 line-clamp-2">{task.description}</p>
                      )}
                    </div>
                    <span className={`px-3 py-1 rounded-full text-sm border flex items-center gap-1 ${getStatusColor(assignment.status)}`}>
                      {getStatusIcon(assignment.status)}
                      {formatStatus(assignment.status)}
                    </span>
                  </div>
                </div>
                <div className="space-y-4">
                  {/* Progress Bar */}
                  <div>
                    <div className="flex items-center justify-between text-sm mb-2">
                      <span className="text-slate-600">Progress</span>
                      <span className="font-medium text-slate-900">{assignment.progress}%</span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full transition-all ${
                          assignment.status === 'completed' ? 'bg-green-500' :
                          assignment.status === 'overdue' ? 'bg-red-500' :
                          'bg-blue-500'
                        }`}
                        style={{ width: `${assignment.progress}%` }}
                      />
                    </div>
                  </div>

                  {/* Task Details */}
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="flex items-center gap-2 text-slate-600">
                      <Calendar className="w-4 h-4" />
                      <div>
                        <div className="text-xs text-slate-500">Assigned</div>
                        <div className="font-medium">{assignment.assignedAt}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 text-slate-600">
                      <Clock className="w-4 h-4" />
                      <div>
                        <div className="text-xs text-slate-500">Duration</div>
                        <div className="font-medium">{assignment.daysToComplete} days</div>
                      </div>
                    </div>
                  </div>

                  {task && (
                    <div className="flex items-center justify-between pt-2 border-t border-slate-200">
                      <span className={`text-xs px-2 py-1 rounded-full border ${priorityColor} border-current`}>
                        {task.priority.toUpperCase()} Priority
                      </span>
                      {assignment.completedAt && (
                        <span className="text-xs text-green-600 flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3" />
                          Completed {assignment.completedAt}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="bg-white p-6 rounded-lg border border-slate-200">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="text-sm text-slate-600">
              Showing {((currentPage - 1) * itemsPerPage) + 1} to {Math.min(currentPage * itemsPerPage, filteredAssignments.length)} of {filteredAssignments.length} tasks
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="px-3 py-1 border border-slate-300 rounded-lg text-sm hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Previous
              </button>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                <button
                  key={page}
                  onClick={() => setCurrentPage(page)}
                  className={`px-3 py-1 border rounded-lg text-sm ${
                    currentPage === page
                      ? 'bg-indigo-600 text-white border-indigo-600'
                      : 'border-slate-300 hover:bg-slate-50'
                  }`}
                >
                  {page}
                </button>
              ))}
              <button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="px-3 py-1 border border-slate-300 rounded-lg text-sm hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}