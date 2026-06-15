import { useState, useEffect } from 'react';
import { Search, Calendar, User, Activity, Trash2, ChevronLeft, ChevronRight, RefreshCw, AlertCircle } from 'lucide-react';
import { useAuth } from '../../context/auth-context';
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/activity';

export default function AuditLogs() {
  const { user } = useAuth();
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterActivityType, setFilterActivityType] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize] = useState(50);
  const [stats, setStats] = useState({
    total: 0,
    successful: 0,
    failed: 0
  });
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  // Determine which endpoint to use based on user role
  const getEndpoint = () => {
    if (user?.role === 'admin' || user?.role === 'analyst') {
      return `${API_BASE_URL}/activities/`;
    } else if (user?.role === 'manager') {
      // For managers, we'll use the all activities endpoint but the backend will filter appropriately
      return `${API_BASE_URL}/activities/`;
    } else {
      // For employees and other roles, use my-activities
      return `${API_BASE_URL}/my-activities/`;
    }
  };

  // Get role-specific description
  const getDescription = () => {
    if (user?.role === 'admin' || user?.role === 'analyst') {
      return 'Track all system activities, user actions, and security events with detailed audit trails';
    } else if (user?.role === 'manager') {
      return 'View your activities and your team members\' activities with detailed audit trails';
    } else {
      return 'Track your system activities and actions with detailed audit trails';
    }
  };

  // Fetch activities from backend
  const fetchActivities = async (page = 1, refresh = false) => {
    try {
      if (refresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);

      const endpoint = getEndpoint();
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      });

      // Add search filter
      if (searchTerm) {
        params.append('search', searchTerm);
      }

      // Add status filter
      if (filterStatus !== 'all') {
        if (filterStatus === 'success') {
          params.append('status_code', '200');
        } else if (filterStatus === 'failed') {
          params.append('status_code', '400');
        }
      }

      // Add activity type filter
      if (filterActivityType !== 'all') {
        params.append('activity_type', filterActivityType);
      }

      const response = await axios.get(`${endpoint}?${params.toString()}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });

      if (response.data.success) {
        setLogs(response.data.data);
        if (response.data.pagination) {
          setTotalPages(response.data.pagination.total_pages);
          setTotalCount(response.data.pagination.total);
          setCurrentPage(response.data.pagination.page);
        }

        // Calculate stats
        const successful = response.data.data.filter(log => log.is_success).length;
        const failed = response.data.data.length - successful;
        setStats({
          total: response.data.pagination?.total || response.data.data.length,
          successful: successful,
          failed: failed
        });
      }
    } catch (err) {
      console.error('Error fetching activities:', err);
      setError(err.response?.data?.message || 'Failed to load audit logs. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Fetch activities on component mount and when filters change
  useEffect(() => {
    fetchActivities(1);
  }, [filterStatus, filterActivityType, searchTerm]);

  // Handle page change
  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setCurrentPage(newPage);
      fetchActivities(newPage);
    }
  };

  // Handle refresh
  const handleRefresh = () => {
    fetchActivities(currentPage, true);
  };

  // Handle delete old activities (admin only)
  const handleDeleteOldLogs = async () => {
    if (user.role != 'admin') {
      alert('Only administrators can delete audit logs.');
      return;
    }

    const days = prompt('Delete logs older than how many days? (Default: 90)');
    const daysToDelete = days ? parseInt(days) : 90;

    if (isNaN(daysToDelete) || daysToDelete < 1) {
      alert('Please enter a valid number of days.');
      return;
    }

    const confirmDelete = confirm(
      `Are you sure you want to delete all audit logs older than ${daysToDelete} days? This action cannot be undone.`
    );

    if (!confirmDelete) return;

    try {
      setDeleteLoading(true);
      const response = await axios.delete(`${API_BASE_URL}/cleanup/`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        },
        data: {
          days: daysToDelete
        }
      });

      if (response.data.success) {
        alert(response.data.message);
        fetchActivities(1); // Refresh the list
      }
    } catch (err) {
      console.error('Error deleting old logs:', err);
      alert(err.response?.data?.message || 'Failed to delete old logs. Please try again.');
    } finally {
      setDeleteLoading(false);
    }
  };

  // Format activity user display
  const formatActivityUser = (activity) => {
    if (!activity.user_details) {
      return 'System';
    }

    // If the activity was performed by the logged-in user, show "You"
    if (user && activity.user === user.id) {
      return 'You';
    }

    return activity.user_details.full_name;
  };

  // Format timestamp
  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString('en-US', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
  };

  // Get status badge class
  const getStatusBadgeClass = (isSuccess) => {
    return isSuccess
      ? 'bg-emerald-100 text-emerald-700'
      : 'bg-red-100 text-red-700';
  };

  // Get unique activity types for filter
  const activityTypes = [
    { value: 'all', label: 'All Activity Types' },
    { value: 'user_login', label: 'User Login' },
    { value: 'user_logout', label: 'User Logout' },
    { value: 'user_create', label: 'User Created' },
    { value: 'user_update', label: 'User Updated' },
    { value: 'user_delete', label: 'User Deleted' },
    { value: 'task_create', label: 'Task Created' },
    { value: 'task_update', label: 'Task Updated' },
    { value: 'task_delete', label: 'Task Deleted' },
    { value: 'task_assignment_create', label: 'Task Assignment Created' },
    { value: 'task_assignment_update', label: 'Task Assignment Updated' },
    { value: 'department_create', label: 'Department Created' },
    { value: 'department_update', label: 'Department Updated' },
    { value: 'dayoff_request_create', label: 'Day-Off Request Created' },
    { value: 'dayoff_request_approve', label: 'Day-Off Request Approved' },
    { value: 'dayoff_request_reject', label: 'Day-Off Request Rejected' },
  ];

  if (loading && !refreshing) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mx-auto mb-2" />
          <p className="text-slate-600">Loading audit logs...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Audit Logs</h1>
          <p className="text-slate-600 mt-1">{getDescription()}</p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          
          {user?.role === 'admin' && (
            <button
              onClick={handleDeleteOldLogs}
              disabled={deleteLoading}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
            >
              <Trash2 className="w-4 h-4" />
              {deleteLoading ? 'Deleting...' : 'Delete Old Logs'}
            </button>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-semibold text-red-900">Error</h3>
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white p-4 rounded-xl shadow-sm border border-slate-200">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by user, description, or endpoint..."
              className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
            />
          </div>

          <select
            value={filterActivityType}
            onChange={(e) => setFilterActivityType(e.target.value)}
            className="px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
          >
            {activityTypes.map(type => (
              <option key={type.value} value={type.value}>{type.label}</option>
            ))}
          </select>

          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
          >
            <option value="all">All Status</option>
            <option value="success">Success Only</option>
            <option value="failed">Failed Only</option>
          </select>
        </div>
      </div>

      {/* Logs Table */}
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">User</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">Activity Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">Description</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">Timestamp</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">IP Address</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">Device</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-8 text-center text-slate-500">
                    No audit logs found.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <User className="w-4 h-4 text-slate-400" />
                        <span className={`font-medium ${
                          user && log.user === user.id ? 'text-indigo-600' : 'text-slate-900'
                        }`}>
                          {formatActivityUser(log)}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <Activity className="w-4 h-4 text-slate-400" />
                        <span className="text-slate-700 text-sm">{log.activity_type_display}</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="text-slate-700 text-sm">
                        {log.description || log.endpoint || 'No description'}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2 text-slate-700 text-sm">
                        <Calendar className="w-4 h-4 text-slate-400" />
                        {formatTimestamp(log.created_at)}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-slate-700 font-mono text-sm">
                      {log.ip_address || 'N/A'}
                    </td>
                    <td className="px-6 py-4 text-slate-700 text-sm">
                      {log.device_type || 'N/A'}
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`px-3 py-1 text-xs font-medium rounded-full ${
                          getStatusBadgeClass(log.is_success)
                        }`}
                      >
                        {log.is_success ? 'Success' : 'Failed'}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="px-6 py-4 border-t border-slate-200 flex items-center justify-between">
            <div className="text-sm text-slate-600">
              Showing page {currentPage} of {totalPages} ({totalCount} total logs)
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="p-2 border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              
              <div className="flex items-center gap-1">
                {[...Array(Math.min(5, totalPages))].map((_, idx) => {
                  let pageNum;
                  if (totalPages <= 5) {
                    pageNum = idx + 1;
                  } else if (currentPage <= 3) {
                    pageNum = idx + 1;
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + idx;
                  } else {
                    pageNum = currentPage - 2 + idx;
                  }

                  return (
                    <button
                      key={pageNum}
                      onClick={() => handlePageChange(pageNum)}
                      className={`px-3 py-1 rounded-lg transition-colors ${
                        currentPage === pageNum
                          ? 'bg-indigo-600 text-white'
                          : 'border border-slate-300 hover:bg-slate-50'
                      }`}
                    >
                      {pageNum}
                    </button>
                  );
                })}
              </div>

              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="p-2 border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard title="Total Actions" value={stats.total.toString()} />
        <StatCard
          title="Successful"
          value={stats.successful.toString()}
          color="emerald"
        />
        <StatCard
          title="Failed"
          value={stats.failed.toString()}
          color="red"
        />
      </div>
    </div>
  );
}

function StatCard({ title, value, color = 'slate' }) {
  const colors = {
    slate: 'bg-slate-50 text-slate-900',
    emerald: 'bg-emerald-50 text-emerald-900',
    red: 'bg-red-50 text-red-900',
  };

  return (
    <div className={`p-6 rounded-xl shadow-sm border border-slate-200 ${colors[color] || colors.slate}`}>
      <div className="text-3xl font-bold mb-1">{value}</div>
      <div className="text-sm">{title}</div>
    </div>
  );
}