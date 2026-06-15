/* eslint-disable no-unused-vars */
/* eslint-disable react-hooks/exhaustive-deps */
import { useState, useEffect, useCallback } from 'react';
import { 
  TrendingUp, TrendingDown, Minus, Users, Target, Award, 
  CheckCircle2, AlertCircle, Calendar, Clock, Filter, 
  Download, Search, ChevronLeft, ChevronRight, Loader2,
  Building2, UserCircle, BarChart2, Activity, Zap,
  Star, Medal, Crown, Briefcase, PieChart, LineChart,
  Eye, EyeOff, RefreshCw, CalendarRange, ArrowUpDown,
  MoreVertical, UserPlus, Edit, Trash2, FileText
} from 'lucide-react';
import { toast } from 'sonner';
import { Toaster } from 'sonner';
import { format, parseISO, isValid, subDays } from 'date-fns';
import { useAuth } from '../../context/auth-context';


// ==================== CONSTANTS ====================
const API_BASE_URL = 'http://127.0.0.1:8000/performance';

const USER_ROLES = {
  ADMIN: 'admin',
  MANAGER: 'manager',
  ANALYST: 'analyst',
  EMPLOYEE: 'employee'
};

const PERFORMANCE_LEVELS = {
  EXCELLENT: { min: 90, max: 100, label: 'Excellent', color: 'bg-green-100 text-green-700 border-green-200', icon: Crown },
  GOOD: { min: 80, max: 89, label: 'Good', color: 'bg-blue-100 text-blue-700 border-blue-200', icon: Star },
  AVERAGE: { min: 70, max: 79, label: 'Average', color: 'bg-yellow-100 text-yellow-700 border-yellow-200', icon: Target },
  NEEDS_IMPROVEMENT: { min: 0, max: 69, label: 'Needs Improvement', color: 'bg-red-100 text-red-700 border-red-200', icon: AlertCircle }
};

const TREND_ICONS = {
  up: { icon: TrendingUp, color: 'text-green-600', bg: 'bg-green-100' },
  down: { icon: TrendingDown, color: 'text-red-600', bg: 'bg-red-100' },
  stable: { icon: Minus, color: 'text-slate-600', bg: 'bg-slate-100' }
};

const DATE_RANGE_OPTIONS = [
  { value: 7, label: 'Last 7 days' },
  { value: 30, label: 'Last 30 days' },
  { value: 90, label: 'Last 90 days' },
  { value: 365, label: 'Last year' }
];

const SORT_OPTIONS = [
  { value: 'completion_rate', label: 'Completion Rate' },
  { value: 'productivity_score', label: 'Productivity Score' },
  { value: 'completed_tasks', label: 'Completed Tasks' },
  { value: 'full_name', label: 'Name' }
];

// ==================== API CLIENT ====================
const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
};

const handleApiError = (error, defaultMessage) => {
  console.error('API Error:', error);
  
  if (error.response?.status === 401) {
    toast.error('Session expired. Please login again.');
    setTimeout(() => {
      window.location.href = '/login';
    }, 2000);
    return;
  }
  
  if (error.response?.status === 403) {
    toast.error('You do not have permission to access this resource.');
    return;
  }
  
  if (error.response?.status === 404) {
    toast.error('Resource not found.');
    return;
  }
  
  const errorMessage = error.response?.data?.message || error.message || defaultMessage;
  toast.error(errorMessage);
};

const apiRequest = async (endpoint, options = {}) => {
  const url = new URL(`${API_BASE_URL}${endpoint}`);
  
  if (options.params) {
    Object.keys(options.params).forEach(key => 
      options.params[key] !== undefined && options.params[key] !== null && options.params[key] !== '' && 
      url.searchParams.append(key, options.params[key])
    );
  }
  
  const response = await fetch(url, {
    method: options.method || 'GET',
    headers: getAuthHeaders(),
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  
  const data = await response.json();
  
  if (!response.ok) {
    const error = new Error(data.message || 'API request failed');
    error.response = {
      status: response.status,
      data: data
    };
    throw error;
  }
  
  return data;
};

const apiGet = (endpoint, params = {}) => apiRequest(endpoint, { method: 'GET', params });
const apiPost = (endpoint, body = {}) => apiRequest(endpoint, { method: 'POST', body });

// ==================== HELPER FUNCTIONS ====================
const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  try {
    const date = typeof dateString === 'string' ? parseISO(dateString) : dateString;
    return isValid(date) ? format(date, 'MMM dd, yyyy') : 'Invalid date';
  } catch {
    return 'Invalid date';
  }
};

const getPerformanceLevel = (score) => {
  if (score >= 90) return PERFORMANCE_LEVELS.EXCELLENT;
  if (score >= 80) return PERFORMANCE_LEVELS.GOOD;
  if (score >= 70) return PERFORMANCE_LEVELS.AVERAGE;
  return PERFORMANCE_LEVELS.NEEDS_IMPROVEMENT;
};

const getPerformanceColor = (score) => getPerformanceLevel(score).color;
const getPerformanceLabel = (score) => getPerformanceLevel(score).label;
const getPerformanceIcon = (score) => getPerformanceLevel(score).icon;

const getTrendInfo = (trend) => TREND_ICONS[trend] || TREND_ICONS.stable;

const calculateStats = (data) => {
  if (!data || data.length === 0) return null;
  
  const avg = data.reduce((sum, item) => sum + (item.productivity_score || 0), 0) / data.length;
  const max = Math.max(...data.map(item => item.productivity_score || 0));
  const min = Math.min(...data.map(item => item.productivity_score || 0));
  
  return { avg: avg.toFixed(1), max, min };
};

// ==================== MAIN COMPONENT ====================
export default function PerformanceAnalytics() {
  const { user, loading: authLoading } = useAuth();
  
  // ==================== STATE ====================
  const [pageLoading, setPageLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('my-performance');
  
  // Data states
  const [myPerformance, setMyPerformance] = useState(null);
  const [myPerformanceTrends, setMyPerformanceTrends] = useState([]);
  const [performances, setPerformances] = useState([]);
  const [organization, setOrganization] = useState(null);
  const [departmentSummaries, setDepartmentSummaries] = useState([]);
  
  // Loading states
  const [loading, setLoading] = useState({
    myPerformance: false,
    allPerformances: false,
    organization: false,
    departments: false,
    export: false
  });
  
  // Filters
  const [filters, setFilters] = useState({
    days: 30,
    search: '',
    departmentId: 'all',
    sortBy: 'completion_rate',
    sortOrder: 'desc'
  });
  
  // Pagination
  const [pagination, setPagination] = useState({
    currentPage: 1,
    totalPages: 1,
    totalItems: 0,
    itemsPerPage: 12
  });
  
  // Selected user for detailed view (managers/admins)
  const [selectedUser, setSelectedUser] = useState(null);
  const [showUserDetail, setShowUserDetail] = useState(false);
  
  // ==================== PERMISSIONS ====================
  const userRole = user?.role;
  const isAdmin = userRole === USER_ROLES.ADMIN;
  const isManager = userRole === USER_ROLES.MANAGER;
  const isAnalyst = userRole === USER_ROLES.ANALYST;
  const isEmployee = userRole === USER_ROLES.EMPLOYEE;
  
  const canViewAll = isAdmin || isAnalyst || isManager;
  const canViewOrganization = isAdmin || isAnalyst;
  const canViewDepartment = isAdmin || isAnalyst || isManager;
  const canExport = isAdmin || isAnalyst || isManager;
  
  // ==================== API CALLS ====================
  const fetchMyPerformance = useCallback(async () => {
    if (!user) return;
    
    setLoading(prev => ({ ...prev, myPerformance: true }));
    try {
      const response = await apiGet('/my-performance/', { days: filters.days });
      
      if (response.success) {
        setMyPerformance(response.data);
        setMyPerformanceTrends(response.trends || []);
      }
    } catch (error) {
      handleApiError(error, 'Failed to load your performance data');
    } finally {
      setLoading(prev => ({ ...prev, myPerformance: false }));
    }
  }, [user, filters.days]);
  
  const fetchAllPerformances = useCallback(async () => {
    if (!canViewAll) return;
    
    setLoading(prev => ({ ...prev, allPerformances: true }));
    try {
      const params = {
        days: filters.days,
        page: pagination.currentPage,
        limit: pagination.itemsPerPage,
        ...(filters.search && { search: filters.search }),
        ...(filters.departmentId !== 'all' && { department_id: filters.departmentId }),
      };
      
      const response = await apiGet('/all/', params);
      
      if (response.success) {
        setPerformances(response.data || []);
        setPagination(prev => ({
          ...prev,
          totalItems: response.total_count || 0,
          totalPages: response.total_pages || 1
        }));
      }
    } catch (error) {
      handleApiError(error, 'Failed to load performance data');
    } finally {
      setLoading(prev => ({ ...prev, allPerformances: false }));
    }
  }, [filters, pagination.currentPage, pagination.itemsPerPage]);
  
  const fetchOrganizationPerformance = useCallback(async () => {
    if (!canViewOrganization) return;
    
    setLoading(prev => ({ ...prev, organization: true }));
    try {
      const response = await apiGet('/organization/', { days: filters.days });
      
      if (response.success) {
        setOrganization(response.data);
      }
    } catch (error) {
      handleApiError(error, 'Failed to load organization performance');
    } finally {
      setLoading(prev => ({ ...prev, organization: false }));
    }
  }, [filters.days]);
  
  const fetchDepartmentSummaries = useCallback(async () => {
    if (!canViewOrganization) return;
    
    setLoading(prev => ({ ...prev, departments: true }));
    try {
      const response = await apiGet('/departments/summaries/', { days: filters.days });
      
      if (response.success) {
        setDepartmentSummaries(response.data || []);
      }
    } catch (error) {
      handleApiError(error, 'Failed to load department summaries');
    } finally {
      setLoading(prev => ({ ...prev, departments: false }));
    }
  }, [filters.days]);
  
  // ==================== INITIALIZATION ====================
  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem('access_token');
    if (!token) {
      toast.error('Please login to access performance analytics');
      window.location.href = '/login';
      return;
    }
    
    if (user) {
      initializeData();
    }
  }, [user]);
  
  useEffect(() => {
    if (!user) return;
    
    if (activeTab === 'my-performance') {
      fetchMyPerformance();
    }
  }, [activeTab, filters.days, user]);
  
  useEffect(() => {
    if (!user) return;
    
    if (activeTab === 'all-performances' && canViewAll) {
      fetchAllPerformances();
    }
  }, [activeTab, filters, pagination.currentPage, user]);
  
  useEffect(() => {
    if (!user) return;
    
    if (activeTab === 'organization' && canViewOrganization) {
      fetchOrganizationPerformance();
      fetchDepartmentSummaries();
    }
  }, [activeTab, filters.days, user]);
  
  const initializeData = async () => {
    setPageLoading(true);
    try {
      // Load initial data based on user role
      if (activeTab === 'my-performance') {
        await fetchMyPerformance();
      } else if (activeTab === 'all-performances' && canViewAll) {
        await fetchAllPerformances();
      } else if (activeTab === 'organization' && canViewOrganization) {
        await fetchOrganizationPerformance();
        await fetchDepartmentSummaries();
      }
    } catch (error) {
      console.error('Error initializing data:', error);
    } finally {
      setPageLoading(false);
    }
  };
  
  // ==================== HANDLERS ====================
  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setPagination(prev => ({ ...prev, currentPage: 1 }));
    setSelectedUser(null);
    setShowUserDetail(false);
  };
  
  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, currentPage: 1 }));
  };
  
  const handlePageChange = (page) => {
    setPagination(prev => ({ ...prev, currentPage: page }));
  };
  
  const handleRefresh = () => {
    if (activeTab === 'my-performance') {
      fetchMyPerformance();
    } else if (activeTab === 'all-performances' && canViewAll) {
      fetchAllPerformances();
    } else if (activeTab === 'organization' && canViewOrganization) {
      fetchOrganizationPerformance();
      fetchDepartmentSummaries();
    }
    toast.success('Data refreshed');
  };
  
  const handleViewUserDetail = (userData) => {
    setSelectedUser(userData);
    setShowUserDetail(true);
  };
  
  const handleExport = async (format = 'csv') => {
    if (!canExport) {
      toast.error('You do not have permission to export data');
      return;
    }
    
    setLoading(prev => ({ ...prev, export: true }));
    try {
      // Prepare data for export based on active tab
      let exportData = [];
      let filename = '';
      
      if (activeTab === 'my-performance' && myPerformance) {
        exportData = [myPerformance];
        filename = `my_performance_${formatDate(new Date())}`;
      } else if (activeTab === 'all-performances') {
        exportData = performances;
        filename = `all_performances_${formatDate(new Date())}`;
      } else if (activeTab === 'organization' && organization) {
        exportData = [organization];
        filename = `organization_performance_${formatDate(new Date())}`;
      }
      
      if (exportData.length === 0) {
        toast.error('No data to export');
        return;
      }
      
      // Convert to CSV
      const headers = Object.keys(exportData[0]).filter(key => 
        typeof exportData[0][key] !== 'object'
      );
      
      let csv = headers.join(',') + '\n';
      exportData.forEach(item => {
        const row = headers.map(header => {
          const value = item[header];
          if (value === null || value === undefined) return '';
          if (typeof value === 'string') return `"${value.replace(/"/g, '""')}"`;
          return value;
        });
        csv += row.join(',') + '\n';
      });
      
      // Download
      const blob = new Blob([csv], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
      
      toast.success('Data exported successfully');
    } catch (error) {
      console.error('Export error:', error);
      toast.error('Failed to export data');
    } finally {
      setLoading(prev => ({ ...prev, export: false }));
    }
  };
  
  // ==================== LOADING STATE ====================
  if (authLoading || pageLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-12 h-12 animate-spin text-indigo-600 mx-auto mb-4" />
          <p className="text-slate-600">Loading performance analytics...</p>
        </div>
      </div>
    );
  }
  
  // ==================== NO ACCESS ====================
  if (!user) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center max-w-md">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Access Denied</h2>
          <p className="text-slate-600 mb-6">Please log in to access performance analytics.</p>
          <button
            onClick={() => window.location.href = '/login'}
            className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }
  
  // ==================== RENDER MY PERFORMANCE ====================
  const renderMyPerformance = () => {
    if (loading.myPerformance) {
      return (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
          <span className="ml-2 text-slate-600">Loading your performance data...</span>
        </div>
      );
    }
    
    if (!myPerformance) {
      return (
        <div className="bg-white rounded-lg border border-slate-200 p-12 text-center">
          <BarChart2 className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-2">No Performance Data</h3>
          <p className="text-slate-600 mb-4">Complete tasks to see your performance metrics.</p>
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 inline-flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      );
    }
    
    const performanceLevel = getPerformanceLevel(myPerformance.productivity_score);
    const PerformanceIcon = performanceLevel.icon;
    const TrendIcon = getTrendInfo(myPerformance.performance_trend).icon;
    const trendColor = getTrendInfo(myPerformance.performance_trend).color;
    
    return (
      <div className="space-y-6">
        {/* Header with controls */}
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <select
              value={filters.days}
              onChange={(e) => handleFilterChange('days', parseInt(e.target.value))}
              className="p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              {DATE_RANGE_OPTIONS.map(option => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
            {myPerformance.period_start && myPerformance.period_end && (
              <span className="text-sm text-slate-500 bg-slate-100 px-3 py-2 rounded-lg">
                <CalendarRange className="w-4 h-4 inline mr-1" />
                {formatDate(myPerformance.period_start)} - {formatDate(myPerformance.period_end)}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            {canExport && (
              <button
                onClick={() => handleExport()}
                disabled={loading.export}
                className="px-4 py-2 border border-slate-300 rounded-lg flex items-center gap-2 hover:bg-slate-50 disabled:opacity-50"
              >
                {loading.export ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Download className="w-4 h-4" />
                )}
                Export
              </button>
            )}
            <button
              onClick={handleRefresh}
              className="p-2 border border-slate-300 rounded-lg hover:bg-slate-50"
              title="Refresh data"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
        
        {/* Welcome Banner */}
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl p-6 text-white">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold mb-2">
                Welcome back, {myPerformance.full_name}!
              </h2>
              <p className="text-indigo-100 flex items-center gap-2">
                <Briefcase className="w-4 h-4" />
                {myPerformance.role} • {myPerformance.department_name || 'No Department'}
              </p>
            </div>
            <div className="text-right">
              <div className="text-5xl font-bold mb-2">{myPerformance.productivity_score}%</div>
              <div className="flex items-center justify-end gap-2 text-indigo-100">
                <span>Productivity Score</span>
                <PerformanceIcon className="w-5 h-5" />
              </div>
            </div>
          </div>
        </div>
        
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-slate-600">Task Completion</h3>
              <CheckCircle2 className="w-5 h-5 text-green-600" />
            </div>
            <div className="text-3xl font-bold text-slate-900">{myPerformance.task_completion_rate}%</div>
            <p className="text-sm text-slate-500 mt-2">
              {myPerformance.completed_tasks} of {myPerformance.total_assigned_tasks} tasks
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-slate-600">On-Time Rate</h3>
              <Clock className="w-5 h-5 text-blue-600" />
            </div>
            <div className="text-3xl font-bold text-slate-900">{myPerformance.on_time_completion_rate}%</div>
            <p className="text-sm text-slate-500 mt-2">Tasks completed on schedule</p>
          </div>
          
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-slate-600">Active Tasks</h3>
              <Zap className="w-5 h-5 text-yellow-600" />
            </div>
            <div className="text-3xl font-bold text-slate-900">{myPerformance.active_tasks}</div>
            <p className="text-sm text-slate-500 mt-2">Currently in progress</p>
          </div>
          
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-slate-600">Work Hours</h3>
              <Briefcase className="w-5 h-5 text-purple-600" />
            </div>
            <div className="text-3xl font-bold text-slate-900">{myPerformance.total_work_hours}</div>
            <p className="text-sm text-slate-500 mt-2">Total hours logged</p>
          </div>
        </div>
        
        {/* Performance Details */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Performance Analysis */}
          <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-slate-900">Performance Analysis</h3>
              <div className="flex items-center gap-3">
                <div className={`flex items-center gap-1 px-3 py-1 rounded-full ${TREND_ICONS[myPerformance.performance_trend]?.bg}`}>
                  <TrendIcon className={`w-4 h-4 ${trendColor}`} />
                  <span className={`text-sm font-medium capitalize ${trendColor}`}>
                    {myPerformance.performance_trend} trend
                  </span>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${performanceLevel.color}`}>
                  {performanceLevel.label}
                </span>
              </div>
            </div>
            
            <div className="space-y-5">
              {/* Productivity Score */}
              <div>
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="font-medium text-slate-700">Productivity Score</span>
                  <span className="font-bold text-indigo-600">{myPerformance.productivity_score}%</span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-3">
                  <div 
                    className="bg-gradient-to-r from-indigo-600 to-purple-600 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${myPerformance.productivity_score}%` }}
                  />
                </div>
                <p className="text-xs text-slate-500 mt-2">
                  Based on task completion (50%), active progress (30%), and on-time performance (20%)
                </p>
              </div>
              
              {/* Task Completion Rate */}
              <div>
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="font-medium text-slate-700">Task Completion Rate</span>
                  <span className="font-bold text-green-600">{myPerformance.task_completion_rate}%</span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-green-600 to-emerald-600 h-2 rounded-full"
                    style={{ width: `${myPerformance.task_completion_rate}%` }}
                  />
                </div>
              </div>
              
              {/* On-Time Completion Rate */}
              <div>
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="font-medium text-slate-700">On-Time Completion Rate</span>
                  <span className="font-bold text-blue-600">{myPerformance.on_time_completion_rate}%</span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-blue-600 to-cyan-600 h-2 rounded-full"
                    style={{ width: `${myPerformance.on_time_completion_rate}%` }}
                  />
                </div>
              </div>
            </div>
            
            {/* Comparison */}
            {myPerformance.comparison_to_dept_avg !== 0 && (
              <div className="mt-6 pt-4 border-t border-slate-200">
                <p className="text-sm">
                  <span className="text-slate-600">vs Department Average: </span>
                  <span className={myPerformance.comparison_to_dept_avg > 0 ? 'text-green-600 font-semibold' : 'text-red-600 font-semibold'}>
                    {myPerformance.comparison_to_dept_avg > 0 ? '+' : ''}{myPerformance.comparison_to_dept_avg}%
                  </span>
                </p>
              </div>
            )}
          </div>
          
          {/* Task Status Summary */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Task Summary</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between py-2 border-b border-slate-100">
                <span className="text-sm text-slate-600">Total Assigned</span>
                <span className="font-semibold text-slate-900">{myPerformance.total_assigned_tasks}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-green-600" />
                  Completed
                </span>
                <span className="font-semibold text-green-600">{myPerformance.completed_tasks}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600 flex items-center gap-2">
                  <Zap className="w-4 h-4 text-blue-600" />
                  Active
                </span>
                <span className="font-semibold text-blue-600">{myPerformance.active_tasks}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600 flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-purple-600" />
                  Scheduled
                </span>
                <span className="font-semibold text-purple-600">{myPerformance.scheduled_tasks}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-red-600" />
                  Overdue
                </span>
                <span className="font-semibold text-red-600">{myPerformance.overdue_tasks}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-orange-600" />
                  Missed
                </span>
                <span className="font-semibold text-orange-600">{myPerformance.missed_tasks}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-600 flex items-center gap-2">
                  <Minus className="w-4 h-4 text-slate-600" />
                  Cancelled
                </span>
                <span className="font-semibold text-slate-600">{myPerformance.cancelled_tasks}</span>
              </div>
              
              <div className="mt-4 pt-4 border-t border-slate-200">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-600">Avg Completion Time</span>
                  <span className="font-semibold text-slate-900">{myPerformance.avg_completion_time_hours} hours</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        {/* Trends Chart Placeholder */}
        {myPerformanceTrends.length > 0 && (
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900 mb-4">Performance Trend</h3>
            <div className="h-64 flex items-center justify-center border border-slate-100 rounded-lg bg-slate-50">
              <LineChart className="w-8 h-8 text-slate-300" />
              <span className="ml-2 text-slate-400">Chart visualization coming soon</span>
            </div>
          </div>
        )}
      </div>
    );
  };
  
  // ==================== RENDER ALL PERFORMANCES ====================
  const renderAllPerformances = () => {
    if (loading.allPerformances && performances.length === 0) {
      return (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
          <span className="ml-2 text-slate-600">Loading performance data...</span>
        </div>
      );
    }
    
    return (
      <div className="space-y-6">
        {/* Filters and Controls */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
              <input
                type="text"
                placeholder="Search employees..."
                value={filters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
            
            {/* Date Range */}
            <select
              value={filters.days}
              onChange={(e) => handleFilterChange('days', parseInt(e.target.value))}
              className="p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
            >
              {DATE_RANGE_OPTIONS.map(option => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
            
            {/* Sort By */}
            <select
              value={filters.sortBy}
              onChange={(e) => handleFilterChange('sortBy', e.target.value)}
              className="p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
            >
              {SORT_OPTIONS.map(option => (
                <option key={option.value} value={option.value}>{option.label}</option>
              ))}
            </select>
            
            {/* Sort Order */}
            <select
              value={filters.sortOrder}
              onChange={(e) => handleFilterChange('sortOrder', e.target.value)}
              className="p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
            >
              <option value="desc">Highest First</option>
              <option value="asc">Lowest First</option>
            </select>
          </div>
          
          {/* Action Buttons */}
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-200">
            <div className="text-sm text-slate-600">
              {pagination.totalItems > 0 && (
                <>Showing {Math.min((pagination.currentPage - 1) * pagination.itemsPerPage + 1, pagination.totalItems)} to {Math.min(pagination.currentPage * pagination.itemsPerPage, pagination.totalItems)} of {pagination.totalItems} employees</>
              )}
            </div>
            <div className="flex items-center gap-2">
              {canExport && (
                <button
                  onClick={() => handleExport()}
                  disabled={loading.export || performances.length === 0}
                  className="px-4 py-2 border border-slate-300 rounded-lg flex items-center gap-2 hover:bg-slate-50 disabled:opacity-50"
                >
                  {loading.export ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Download className="w-4 h-4" />
                  )}
                  Export
                </button>
              )}
              <button
                onClick={handleRefresh}
                className="p-2 border border-slate-300 rounded-lg hover:bg-slate-50"
                title="Refresh data"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
        
        {/* Performance Grid */}
        {performances.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
            <Users className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-slate-900 mb-2">No Performance Data</h3>
            <p className="text-slate-600">No employees have performance data for the selected period.</p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {performances.map((perf) => {
                const level = getPerformanceLevel(perf.productivity_score);
                const Icon = level.icon;
                const TrendIcon = getTrendInfo(perf.performance_trend).icon;
                const trendColor = getTrendInfo(perf.performance_trend).color;
                
                return (
                  <div 
                    key={perf.user_id} 
                    className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-all cursor-pointer"
                    onClick={() => handleViewUserDetail(perf)}
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="flex-shrink-0 h-12 w-12 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-full flex items-center justify-center">
                          <UserCircle className="w-8 h-8 text-indigo-600" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-slate-900">{perf.full_name}</h3>
                          <p className="text-xs text-slate-500 flex items-center gap-1">
                            <Briefcase className="w-3 h-3" />
                            {perf.department_name || 'No Department'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className={`p-1 rounded-full ${TREND_ICONS[perf.performance_trend]?.bg}`}>
                          <TrendIcon className={`w-4 h-4 ${trendColor}`} />
                        </div>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${level.color}`}>
                          {level.label}
                        </span>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      {/* Productivity Bar */}
                      <div>
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="text-slate-600">Productivity</span>
                          <span className="font-semibold">{perf.productivity_score}%</span>
                        </div>
                        <div className="w-full bg-slate-200 rounded-full h-1.5">
                          <div 
                            className="bg-gradient-to-r from-indigo-600 to-purple-600 h-1.5 rounded-full"
                            style={{ width: `${perf.productivity_score}%` }}
                          />
                        </div>
                      </div>
                      
                      {/* Completion Bar */}
                      <div>
                        <div className="flex items-center justify-between text-xs mb-1">
                          <span className="text-slate-600">Completion</span>
                          <span className="font-semibold">{perf.task_completion_rate}%</span>
                        </div>
                        <div className="w-full bg-slate-200 rounded-full h-1.5">
                          <div 
                            className="bg-gradient-to-r from-green-600 to-emerald-600 h-1.5 rounded-full"
                            style={{ width: `${perf.task_completion_rate}%` }}
                          />
                        </div>
                      </div>
                      
                      {/* Task Stats */}
                      <div className="flex items-center justify-between text-xs pt-2 border-t border-slate-100">
                        <span className="text-slate-600">Tasks</span>
                        <div className="flex gap-3">
                          <span className="text-green-600 font-medium">{perf.completed_tasks} done</span>
                          <span className="text-blue-600 font-medium">{perf.active_tasks} active</span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
            
            {/* Pagination */}
            {pagination.totalPages > 1 && (
              <div className="flex items-center justify-between bg-white p-4 rounded-xl border border-slate-200">
                <div className="text-sm text-slate-600">
                  Page {pagination.currentPage} of {pagination.totalPages}
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handlePageChange(pagination.currentPage - 1)}
                    disabled={pagination.currentPage === 1}
                    className="p-2 border border-slate-300 rounded-lg disabled:opacity-50 hover:bg-slate-50"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <span className="px-4 py-2 bg-indigo-600 text-white rounded-lg">
                    {pagination.currentPage}
                  </span>
                  <button
                    onClick={() => handlePageChange(pagination.currentPage + 1)}
                    disabled={pagination.currentPage === pagination.totalPages}
                    className="p-2 border border-slate-300 rounded-lg disabled:opacity-50 hover:bg-slate-50"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </>
        )}
        
        {/* User Detail Modal */}
        {showUserDetail && selectedUser && (
          <UserDetailModal
            user={selectedUser}
            onClose={() => setShowUserDetail(false)}
            canExport={canExport}
          />
        )}
      </div>
    );
  };
  
  // ==================== RENDER ORGANIZATION PERFORMANCE ====================
  const renderOrganizationPerformance = () => {
    if (loading.organization || loading.departments) {
      return (
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
          <span className="ml-2 text-slate-600">Loading organization data...</span>
        </div>
      );
    }
    
    if (!organization) {
      return (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <Building2 className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-2">No Organization Data</h3>
          <p className="text-slate-600 mb-4">Unable to load organization performance metrics.</p>
          <button
            onClick={handleRefresh}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 inline-flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
        </div>
      );
    }
    
    return (
      <div className="space-y-6">
        {/* Header Controls */}
        <div className="flex items-center justify-between">
          <select
            value={filters.days}
            onChange={(e) => handleFilterChange('days', parseInt(e.target.value))}
            className="p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500"
          >
            {DATE_RANGE_OPTIONS.map(option => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
          
          <div className="flex items-center gap-2">
            {canExport && (
              <button
                onClick={() => handleExport()}
                disabled={loading.export}
                className="px-4 py-2 border border-slate-300 rounded-lg flex items-center gap-2 hover:bg-slate-50 disabled:opacity-50"
              >
                {loading.export ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Download className="w-4 h-4" />
                )}
                Export
              </button>
            )}
            <button
              onClick={handleRefresh}
              className="p-2 border border-slate-300 rounded-lg hover:bg-slate-50"
              title="Refresh data"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>
        
        {/* Organization Overview */}
        <div className="bg-gradient-to-r from-indigo-600 to-purple-600 rounded-xl p-8 text-white">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-bold mb-2">Organization Performance</h2>
              <p className="text-indigo-100 flex items-center gap-2">
                <Building2 className="w-4 h-4" />
                {organization.total_employees} Employees • {organization.total_departments} Departments
              </p>
            </div>
            <div className="text-right">
              <div className="text-5xl font-bold mb-2">{organization.overall_completion_rate}%</div>
              <div className="text-indigo-100">Overall Completion Rate</div>
            </div>
          </div>
        </div>
        
        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-slate-600">Total Employees</h3>
              <Users className="w-5 h-5 text-indigo-600" />
            </div>
            <div className="text-3xl font-bold text-slate-900">{organization.total_employees}</div>
            <p className="text-xs text-slate-500 mt-2">Active workforce</p>
          </div>
          
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-slate-600">Tasks Completed</h3>
              <CheckCircle2 className="w-5 h-5 text-green-600" />
            </div>
            <div className="text-3xl font-bold text-slate-900">{organization.total_tasks_completed}</div>
            <p className="text-xs text-slate-500 mt-2">
              of {organization.total_tasks_assigned} assigned
            </p>
          </div>
          
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-slate-600">Active Tasks</h3>
              <Zap className="w-5 h-5 text-blue-600" />
            </div>
            <div className="text-3xl font-bold text-slate-900">{organization.total_active_tasks}</div>
            <p className="text-xs text-slate-500 mt-2">Currently in progress</p>
          </div>
          
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-slate-600">Missed Tasks</h3>
              <AlertCircle className="w-5 h-5 text-red-600" />
            </div>
            <div className="text-3xl font-bold text-slate-900">{organization.total_missed_tasks}</div>
            <p className="text-xs text-slate-500 mt-2">Need attention</p>
          </div>
        </div>
        
        {/* Department Performance */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <h3 className="text-lg font-semibold text-slate-900 mb-6">Department Performance</h3>
          <div className="space-y-4">
            {departmentSummaries.length > 0 ? (
              departmentSummaries.map((dept) => (
                <div key={dept.department_id} className="p-4 bg-slate-50 rounded-lg">
                  <div className="flex flex-wrap items-center justify-between gap-4 mb-3">
                    <div className="flex items-center gap-3">
                      <Building2 className="w-5 h-5 text-indigo-600" />
                      <div>
                        <h4 className="font-semibold text-slate-900">{dept.department_name}</h4>
                        <p className="text-xs text-slate-500">{dept.employee_count} employees</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="text-right">
                        <div className="text-xl font-bold text-indigo-600">{dept.avg_task_completion_rate}%</div>
                        <p className="text-xs text-slate-500">Completion Rate</p>
                      </div>
                      <div className="text-right">
                        <div className="text-xl font-bold text-slate-900">{dept.avg_productivity_score}%</div>
                        <p className="text-xs text-slate-500">Productivity</p>
                      </div>
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4 mt-2">
                    <div className="text-center p-2 bg-white rounded-lg">
                      <p className="text-xs text-slate-500">Completed</p>
                      <p className="text-sm font-semibold text-green-600">{dept.completed_tasks}</p>
                    </div>
                    <div className="text-center p-2 bg-white rounded-lg">
                      <p className="text-xs text-slate-500">Active</p>
                      <p className="text-sm font-semibold text-blue-600">{dept.active_tasks}</p>
                    </div>
                    <div className="text-center p-2 bg-white rounded-lg">
                      <p className="text-xs text-slate-500">Missed</p>
                      <p className="text-sm font-semibold text-red-600">{dept.missed_tasks}</p>
                    </div>
                  </div>
                  
                  {/* Top Performers */}
                  {dept.top_performers?.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-slate-200">
                      <p className="text-xs text-slate-600 mb-2 flex items-center gap-1">
                        <Crown className="w-3 h-3 text-yellow-600" />
                        Top Performers:
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {dept.top_performers.map((performer, idx) => (
                          <span 
                            key={idx} 
                            className="inline-flex items-center px-2 py-1 bg-indigo-100 text-indigo-700 rounded-full text-xs"
                          >
                            <Star className="w-3 h-3 mr-1" />
                            {performer.full_name} ({performer.completion_rate}%)
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))
            ) : (
              <p className="text-center text-slate-500 py-4">No department data available</p>
            )}
          </div>
        </div>
        
        {/* Top Employees */}
        {organization.top_employees?.length > 0 && (
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
            <h3 className="text-lg font-semibold text-slate-900 mb-6">Top Performing Employees</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {organization.top_employees.map((employee, index) => {
                const level = getPerformanceLevel(employee.task_completion_rate);
                
                return (
                  <div key={employee.user_id} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                    <div className="flex-shrink-0 h-12 w-12 bg-gradient-to-br from-yellow-100 to-amber-100 rounded-full flex items-center justify-center">
                      {index === 0 ? (
                        <Crown className="w-6 h-6 text-yellow-600" />
                      ) : index === 1 ? (
                        <Medal className="w-6 h-6 text-slate-600" />
                      ) : index === 2 ? (
                        <Award className="w-6 h-6 text-amber-600" />
                      ) : (
                        <Star className="w-6 h-6 text-indigo-600" />
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h4 className="font-semibold text-slate-900">{employee.full_name}</h4>
                        <span className={`text-sm font-bold ${level.color.split(' ')[1]}`}>
                          {employee.task_completion_rate}%
                        </span>
                      </div>
                      <p className="text-xs text-slate-500 flex items-center gap-1">
                        <Building2 className="w-3 h-3" />
                        {employee.department_name || 'No Department'}
                      </p>
                      <p className="text-xs text-slate-600 mt-1">
                        {employee.completed_tasks} tasks completed
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    );
  };
  
  // ==================== MAIN RENDER ====================
  return (
    <div className="space-y-6 p-6">
      <Toaster position="top-center" richColors />
      
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Performance Analytics</h1>
          <p className="text-slate-600 mt-1">
            {isEmployee && 'Track your individual performance metrics and productivity scores'}
            {isManager && 'Monitor your team\'s performance and identify top performers'}
            {isAdmin && 'Comprehensive performance analytics across the entire organization'}
            {isAnalyst && 'Analyze workforce performance trends and department metrics'}
          </p>
        </div>
      </div>
      
      {/* Tabs */}
      <div className="border-b border-slate-200">
        <div className="flex gap-6">
          <button
            onClick={() => handleTabChange('my-performance')}
            className={`px-1 py-3 border-b-2 transition-colors flex items-center gap-2 ${
              activeTab === 'my-performance'
                ? 'border-indigo-600 text-indigo-600 font-semibold'
                : 'border-transparent text-slate-600 hover:text-slate-900'
            }`}
          >
            <UserCircle className="w-4 h-4" />
            My Performance
          </button>
          
          {canViewAll && (
            <button
              onClick={() => handleTabChange('all-performances')}
              className={`px-1 py-3 border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === 'all-performances'
                  ? 'border-indigo-600 text-indigo-600 font-semibold'
                  : 'border-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              <Users className="w-4 h-4" />
              {isManager ? 'Team Performance' : 'All Employees'}
            </button>
          )}
          
          {canViewOrganization && (
            <button
              onClick={() => handleTabChange('organization')}
              className={`px-1 py-3 border-b-2 transition-colors flex items-center gap-2 ${
                activeTab === 'organization'
                  ? 'border-indigo-600 text-indigo-600 font-semibold'
                  : 'border-transparent text-slate-600 hover:text-slate-900'
              }`}
            >
              <Building2 className="w-4 h-4" />
              Organization
            </button>
          )}
        </div>
      </div>
      
      {/* Content */}
      <div className="mt-6">
        {activeTab === 'my-performance' && renderMyPerformance()}
        {activeTab === 'all-performances' && canViewAll && renderAllPerformances()}
        {activeTab === 'organization' && canViewOrganization && renderOrganizationPerformance()}
      </div>
    </div>
  );
}

// ==================== USER DETAIL MODAL ====================
function UserDetailModal({ user, onClose, canExport }) {
  const [loading, setLoading] = useState(false);
  const [userDetails, setUserDetails] = useState(null);
  
  useEffect(() => {
    fetchUserDetails();
  }, [user.user_id]);
  
  const fetchUserDetails = async () => {
    setLoading(true);
    try {
      const response = await apiGet(`/users/${user.user_id}/`, { days: 30 });
      if (response.success) {
        setUserDetails(response.data);
      }
    } catch (error) {
      handleApiError(error, 'Failed to load user details');
    } finally {
      setLoading(false);
    }
  };
  
  if (!user) return null;
  
  const level = getPerformanceLevel(user.productivity_score);
  const Icon = level.icon;
  
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-xl font-bold text-slate-900">Employee Performance Details</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center h-48">
              <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
            </div>
          ) : (
            <div className="space-y-6">
              {/* User Info */}
              <div className="flex items-center gap-4">
                <div className="h-16 w-16 bg-gradient-to-br from-indigo-100 to-purple-100 rounded-full flex items-center justify-center">
                  <UserCircle className="w-10 h-10 text-indigo-600" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">{user.full_name}</h3>
                  <p className="text-sm text-slate-600 flex items-center gap-2 mt-1">
                    <Briefcase className="w-4 h-4" />
                    {user.department_name || 'No Department'} • {user.role}
                  </p>
                </div>
              </div>
              
              {/* Performance Summary */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-slate-50 rounded-lg">
                  <p className="text-sm text-slate-600 mb-1">Productivity Score</p>
                  <div className="flex items-center gap-2">
                    <span className="text-2xl font-bold text-indigo-600">{user.productivity_score}%</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${level.color}`}>
                      {level.label}
                    </span>
                  </div>
                </div>
                <div className="p-4 bg-slate-50 rounded-lg">
                  <p className="text-sm text-slate-600 mb-1">Completion Rate</p>
                  <span className="text-2xl font-bold text-green-600">{user.task_completion_rate}%</span>
                </div>
              </div>
              
              {/* Task Stats */}
              <div className="space-y-3">
                <h4 className="font-semibold text-slate-900">Task Statistics</h4>
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex justify-between p-2 bg-slate-50 rounded">
                    <span className="text-sm text-slate-600">Completed</span>
                    <span className="font-semibold text-green-600">{user.completed_tasks}</span>
                  </div>
                  <div className="flex justify-between p-2 bg-slate-50 rounded">
                    <span className="text-sm text-slate-600">Active</span>
                    <span className="font-semibold text-blue-600">{user.active_tasks}</span>
                  </div>
                  <div className="flex justify-between p-2 bg-slate-50 rounded">
                    <span className="text-sm text-slate-600">Overdue</span>
                    <span className="font-semibold text-red-600">{user.overdue_tasks}</span>
                  </div>
                  <div className="flex justify-between p-2 bg-slate-50 rounded">
                    <span className="text-sm text-slate-600">Missed</span>
                    <span className="font-semibold text-orange-600">{user.missed_tasks}</span>
                  </div>
                </div>
              </div>
              
              {/* Performance Metrics */}
              <div className="space-y-3">
                <h4 className="font-semibold text-slate-900">Performance Metrics</h4>
                <div className="space-y-2">
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-600">On-Time Rate</span>
                      <span className="font-medium">{user.on_time_completion_rate}%</span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2">
                      <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${user.on_time_completion_rate}%` }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-600">Avg Completion Time</span>
                      <span className="font-medium">{user.avg_completion_time_hours} hours</span>
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-600">Total Work Hours</span>
                      <span className="font-medium">{user.total_work_hours} hours</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}