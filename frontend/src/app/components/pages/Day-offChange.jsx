/* eslint-disable react-hooks/exhaustive-deps */
/* eslint-disable no-unused-vars */
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import {
  Search, RefreshCw, X, Save, Plus, Edit, Trash2,
  CheckCircle, XCircle, AlertCircle, Clock, Activity,
  ChevronLeft, ChevronRight, ArrowUpDown, Filter,
  FileText, Calendar, User, BarChart3, TrendingUp,
  ListTodo, CheckSquare, Square, AlertTriangle,
  Eye, MoreVertical, Download, Upload,
  Play, StopCircle, Pause, Users, RotateCcw,
  Zap, Shield, Target, CalendarDays, UserCheck,
  Briefcase, Building, Mail, Phone, MapPin,
  Check, ExternalLink, Calendar as CalendarIcon,
  Clock as ClockIcon, AlertOctagon, Info,
  Loader2, ArrowRight, ArrowLeft, Hash,
  Crown, Star, TrendingDown, EyeOff,
  ShieldCheck, ShieldAlert, ShieldOff,
  Send, Ban, UserX, CalendarClock, ThumbsUp, ThumbsDown,
  UserCircle, AtSign, BadgeCheck, BadgeX
} from 'lucide-react';
import { useAuth } from '../../context/auth-context';
import { toast } from 'sonner';
import { format, parseISO, isValid } from 'date-fns';

// ==================== CONSTANTS ====================
const REQUEST_STATUSES = {
  PENDING: 'pending',
  APPROVED: 'approved',
  REJECTED: 'rejected',
  CANCELLED: 'cancelled'
};

const DAY_CHOICES = [
  { value: 'monday', label: 'Monday' },
  { value: 'tuesday', label: 'Tuesday' },
  { value: 'wednesday', label: 'Wednesday' },
  { value: 'thursday', label: 'Thursday' },
  { value: 'friday', label: 'Friday' },
  { value: 'saturday', label: 'Saturday' },
  { value: 'sunday', label: 'Sunday' },
  { value: 'none', label: 'No Day Off' }
];

const USER_ROLES = {
  ADMIN: 'admin',
  MANAGER: 'manager',
  ANALYST: 'analyst',
  EMPLOYEE: 'employee'
};

// ==================== HELPER FUNCTIONS ====================
const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  try {
    const date = parseISO(dateString);
    return isValid(date) ? format(date, 'MMM dd, yyyy') : 'Invalid date';
  } catch {
    return 'Invalid date';
  }
};

const formatDateTime = (dateTimeString) => {
  if (!dateTimeString) return 'N/A';
  try {
    const date = parseISO(dateTimeString);
    return isValid(date) ? format(date, 'MMM dd, yyyy HH:mm') : 'Invalid date';
  } catch {
    return 'Invalid date';
  }
};

const getStatusColor = (status) => {
  switch (status) {
    case REQUEST_STATUSES.PENDING:
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    case REQUEST_STATUSES.APPROVED:
      return 'bg-green-100 text-green-800 border-green-200';
    case REQUEST_STATUSES.REJECTED:
      return 'bg-red-100 text-red-800 border-red-200';
    case REQUEST_STATUSES.CANCELLED:
      return 'bg-gray-100 text-gray-800 border-gray-200';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

const getStatusIcon = (status) => {
  switch (status) {
    case REQUEST_STATUSES.PENDING:
      return Clock;
    case REQUEST_STATUSES.APPROVED:
      return CheckCircle;
    case REQUEST_STATUSES.REJECTED:
      return XCircle;
    case REQUEST_STATUSES.CANCELLED:
      return Ban;
    default:
      return AlertCircle;
  }
};

const getDayLabel = (dayValue) => {
  const day = DAY_CHOICES.find(d => d.value === dayValue);
  return day ? day.label : dayValue;
};

// ==================== MAIN COMPONENT ====================
export default function DayOffChangeRequestManagement() {
  const { user, api } = useAuth();
  
  // ==================== STATE MANAGEMENT ====================
  // Loading states
  const [loading, setLoading] = useState({
    initial: true,
    action: false
  });

  // Data states
  const [requests, setRequests] = useState([]);
  const [users, setUsers] = useState([]);

  // UI states
  const [activeView, setActiveView] = useState('all');

  // Modal states
  const [modals, setModals] = useState({
    create: false,
    details: false,
    approve: false,
    reject: false,
    cancel: false,
    delete: false,
    update: false,
    pendingWarning: false
  });

  // Selected items
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [selectedRequestForAction, setSelectedRequestForAction] = useState(null);

  // Form states
  const [createForm, setCreateForm] = useState({
    reason: '',
    requested_day_off: '',
    effective_from: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
  });

  const [updateForm, setUpdateForm] = useState({
    reason: '',
    requested_day_off: '',
    effective_from: ''
  });

  const [actionForm, setActionForm] = useState({
    notes: '',
    reason: ''
  });

  const [formErrors, setFormErrors] = useState({});
  const [pendingRequests, setPendingRequests] = useState([]);

  // Filter states
  const [filters, setFilters] = useState({
    search: '',
    status: 'all',
    user_id: ''
  });

  // Pagination
  const [pagination, setPagination] = useState({
    currentPage: 1,
    rowsPerPage: 10,
    totalPages: 1,
    totalItems: 0
  });

  // Sort
  const [sortConfig, setSortConfig] = useState({
    key: 'created_at',
    direction: 'desc'
  });

  // Dashboard stats
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    approved: 0,
    rejected: 0,
    cancelled: 0
  });

  // ==================== PERMISSIONS ====================
  const permissions = {
    isAdmin: user?.role === USER_ROLES.ADMIN,
    isManager: user?.role === USER_ROLES.MANAGER,
    isAnalyst: user?.role === USER_ROLES.ANALYST,
    isEmployee: user?.role === USER_ROLES.EMPLOYEE,
    
    canCreate: user?.role === USER_ROLES.EMPLOYEE,
    canViewAll: [USER_ROLES.ADMIN, USER_ROLES.MANAGER, USER_ROLES.ANALYST].includes(user?.role),
    canApproveReject: [USER_ROLES.ADMIN, USER_ROLES.MANAGER].includes(user?.role),
    canDeleteAny: [USER_ROLES.ADMIN, USER_ROLES.MANAGER].includes(user?.role),
    canUpdateOwn: user?.role === USER_ROLES.EMPLOYEE,
    canCancelOwn: user?.role === USER_ROLES.EMPLOYEE,
    canDeleteOwn: user?.role === USER_ROLES.EMPLOYEE,
    canViewEmployeeDetails: [USER_ROLES.ADMIN, USER_ROLES.MANAGER, USER_ROLES.ANALYST].includes(user?.role)
  };

  // ==================== API CLIENT ====================
  const REQUEST_BASE_URL = 'http://127.0.0.1:8000/request';

  const apiClient = {
    requests: {
      getAll: async (params = {}) => {
        try {
          const queryParams = new URLSearchParams();
          if (params.status) queryParams.append('status', params.status);
          if (params.user_id) queryParams.append('user_id', params.user_id);
          
          const response = await api.get(`${REQUEST_BASE_URL}/all/?${queryParams}`);
          return response.data;
        } catch (error) {
          console.error('Error fetching all requests:', error);
          throw error;
        }
      },

      getMyRequests: async (params = {}) => {
        try {
          const queryParams = new URLSearchParams();
          if (params.status) queryParams.append('status', params.status);
          
          const response = await api.get(`${REQUEST_BASE_URL}/my-requests/?${queryParams}`);
          return response.data;
        } catch (error) {
          console.error('Error fetching my requests:', error);
          throw error;
        }
      },

      getByUser: async (userId, params = {}) => {
        try {
          const queryParams = new URLSearchParams();
          if (params.status) queryParams.append('status', params.status);
          
          const response = await api.get(`${REQUEST_BASE_URL}/user/${userId}/?${queryParams}`);
          return response.data;
        } catch (error) {
          console.error('Error fetching user requests:', error);
          throw error;
        }
      },

      getById: async (requestId) => {
        try {
          const response = await api.get(`${REQUEST_BASE_URL}/${requestId}/`);
          return response.data;
        } catch (error) {
          console.error('Error fetching request by ID:', error);
          throw error;
        }
      },

      create: async (data) => {
        try {
          const response = await api.post(`${REQUEST_BASE_URL}/create/`, data);
          return response.data;
        } catch (error) {
          console.error('Error creating request:', error);
          throw error;
        }
      },

      update: async (requestId, data) => {
        try {
          const response = await api.patch(`${REQUEST_BASE_URL}/${requestId}/update/`, data);
          return response.data;
        } catch (error) {
          console.error('Error updating request:', error);
          throw error;
        }
      },

      approve: async (requestId, notes = '') => {
        try {
          const response = await api.post(`${REQUEST_BASE_URL}/${requestId}/approve/`, { notes });
          return response.data;
        } catch (error) {
          console.error('Error approving request:', error);
          throw error;
        }
      },

      reject: async (requestId, notes = '') => {
        try {
          const response = await api.post(`${REQUEST_BASE_URL}/${requestId}/reject/`, { notes });
          return response.data;
        } catch (error) {
          console.error('Error rejecting request:', error);
          throw error;
        }
      },

      cancel: async (requestId, reason = '') => {
        try {
          const response = await api.post(`${REQUEST_BASE_URL}/${requestId}/cancel/`, { reason });
          return response.data;
        } catch (error) {
          console.error('Error cancelling request:', error);
          throw error;
        }
      },

      delete: async (requestId) => {
        try {
          const response = await api.delete(`${REQUEST_BASE_URL}/${requestId}/delete/`);
          return response.data;
        } catch (error) {
          console.error('Error deleting request:', error);
          throw error;
        }
      },

      getStats: async () => {
        try {
          const response = await api.get(`${REQUEST_BASE_URL}/stats/`);
          return response.data;
        } catch (error) {
          console.error('Error fetching stats:', error);
          throw error;
        }
      },

      checkPendingRequests: async () => {
        try {
          const response = await api.get(`${REQUEST_BASE_URL}/my-requests/?status=pending`);
          return response.data;
        } catch (error) {
          console.error('Error checking pending requests:', error);
          throw error;
        }
      }
    },

    users: {
      getAll: async () => {
        try {
          const response = await api.get('http://127.0.0.1:8000/users/');
          return response.data;
        } catch (error) {
          console.error('Error fetching users:', error);
          throw error;
        }
      }
    }
  };

  // ==================== INITIALIZATION ====================
  useEffect(() => {
    if (user) {
      loadInitialData();
    }
  }, [user]);

  const loadInitialData = async () => {
    setLoading(prev => ({ ...prev, initial: true }));
    try {
      // Load requests based on role
      await loadRequests();
      
      // Load users for admin/manager/analyst filters
      if (permissions.canViewAll) {
        await loadUsers();
      }
      
      // Load stats for admin/manager/analyst
      if (permissions.canViewAll) {
        await loadStats();
      }

      // Check for pending requests for employees
      if (permissions.isEmployee) {
        await checkPendingRequests();
      }
    } catch (error) {
      console.error('Error loading initial data:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(prev => ({ ...prev, initial: false }));
    }
  };

  const loadRequests = async (status = filters.status !== 'all' ? filters.status : null) => {
    try {
      let response;
      
      if (permissions.canViewAll) {
        // Admin, Manager, Analyst can see all requests
        response = await apiClient.requests.getAll({ 
          status,
          user_id: filters.user_id || undefined
        });
        setRequests(response.requests || []);
      } else {
        // Employees see only their own requests
        response = await apiClient.requests.getMyRequests({ status });
        setRequests(response.requests || []);
      }
      
      // Update stats based on loaded requests
      calculateStats(response.requests || []);
      
      // Update pagination
      setPagination(prev => ({
        ...prev,
        totalItems: response.count || (response.requests?.length || 0),
        totalPages: Math.ceil((response.count || (response.requests?.length || 0)) / prev.rowsPerPage)
      }));
      
    } catch (error) {
      console.error('Error loading requests:', error);
      toast.error('Failed to load requests');
    }
  };

  const loadUsers = async () => {
    try {
      const response = await apiClient.users.getAll();
      setUsers(response.users || []);
    } catch (error) {
      console.error('Error loading users:', error);
    }
  };

  const loadStats = async () => {
    try {
      const response = await apiClient.requests.getStats();
      setStats(response);
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const calculateStats = (requestsData) => {
    const total = requestsData.length;
    const pending = requestsData.filter(r => r.status === REQUEST_STATUSES.PENDING).length;
    const approved = requestsData.filter(r => r.status === REQUEST_STATUSES.APPROVED).length;
    const rejected = requestsData.filter(r => r.status === REQUEST_STATUSES.REJECTED).length;
    const cancelled = requestsData.filter(r => r.status === REQUEST_STATUSES.CANCELLED).length;

    setStats({
      total,
      pending,
      approved,
      rejected,
      cancelled
    });
  };

  // Check for existing pending requests
  const checkPendingRequests = async () => {
    try {
      const response = await apiClient.requests.checkPendingRequests();
      const pendingList = response.requests || [];
      setPendingRequests(pendingList);
      return pendingList;
    } catch (error) {
      console.error('Error checking pending requests:', error);
      return [];
    }
  };

  // ==================== FILTERING & SORTING ====================
  const filteredRequests = useMemo(() => {
    let filtered = [...requests];

    // Search filter
    if (filters.search) {
      const term = filters.search.toLowerCase();
      filtered = filtered.filter(request =>
        request.user_details?.full_name?.toLowerCase().includes(term) ||
        request.user_details?.email?.toLowerCase().includes(term) ||
        request.reason?.toLowerCase().includes(term)
      );
    }

    // Sort
    if (sortConfig.key) {
      filtered.sort((a, b) => {
        let aValue = a[sortConfig.key];
        let bValue = b[sortConfig.key];

        // Handle nested values
        if (sortConfig.key === 'user_name') {
          aValue = a.user_name || '';
          bValue = b.user_name || '';
        } else if (sortConfig.key === 'effective_from') {
          aValue = a.effective_from || '';
          bValue = b.effective_from || '';
        }

        if (aValue < bValue) {
          return sortConfig.direction === 'asc' ? -1 : 1;
        }
        if (aValue > bValue) {
          return sortConfig.direction === 'asc' ? 1 : -1;
        }
        return 0;
      });
    }

    return filtered;
  }, [requests, filters.search, sortConfig]);

  // Pagination
  const paginatedRequests = useMemo(() => {
    const startIndex = (pagination.currentPage - 1) * pagination.rowsPerPage;
    const endIndex = startIndex + pagination.rowsPerPage;
    return filteredRequests.slice(startIndex, endIndex);
  }, [filteredRequests, pagination.currentPage, pagination.rowsPerPage]);

  // ==================== EVENT HANDLERS ====================
  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const handlePageChange = (page) => {
    setPagination(prev => ({ ...prev, currentPage: page }));
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, currentPage: 1 }));
  };

  const applyFilters = () => {
    loadRequests();
  };

  const resetFilters = () => {
    setFilters({
      search: '',
      status: 'all',
      user_id: ''
    });
    setPagination(prev => ({ ...prev, currentPage: 1 }));
    loadRequests(null);
  };

  // ==================== MODAL HANDLERS ====================
  const openModal = async (modalName, request = null) => {
    // For create modal, check if user already has pending requests
    if (modalName === 'create' && permissions.isEmployee) {
      const pendingList = await checkPendingRequests();
      if (pendingList.length > 0) {
        setPendingRequests(pendingList);
        setModals(prev => ({ ...prev, pendingWarning: true }));
        return;
      }
    }

    setModals(prev => ({ ...prev, [modalName]: true }));
    
    switch (modalName) {
      case 'create':
        setCreateForm({
          reason: '',
          requested_day_off: '',
          effective_from: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
        });
        setFormErrors({});
        break;
        
      case 'details':
        setSelectedRequest(request);
        break;
        
      case 'update':
        setSelectedRequest(request);
        setUpdateForm({
          reason: request.reason || '',
          requested_day_off: request.requested_day_off || '',
          effective_from: request.effective_from || ''
        });
        setFormErrors({});
        break;
        
      case 'approve':
      case 'reject':
      case 'cancel':
        setSelectedRequestForAction(request);
        setActionForm({ notes: '', reason: '' });
        break;
        
      case 'delete':
        setSelectedRequestForAction(request);
        break;
        
      default:
        break;
    }
  };

  const closeModal = (modalName) => {
    setModals(prev => ({ ...prev, [modalName]: false }));
    
    // Clear selected items
    if (modalName === 'details') {
      setSelectedRequest(null);
    }
    if (['approve', 'reject', 'cancel', 'delete'].includes(modalName)) {
      setSelectedRequestForAction(null);
      setActionForm({ notes: '', reason: '' });
    }
    if (modalName === 'update') {
      setSelectedRequest(null);
      setUpdateForm({ reason: '', requested_day_off: '', effective_from: '' });
    }
    if (modalName === 'create') {
      setCreateForm({
        reason: '',
        requested_day_off: '',
        effective_from: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]
      });
    }
    if (modalName === 'pendingWarning') {
      setPendingRequests([]);
    }
    
    setFormErrors({});
  };

  // ==================== ACTION HANDLERS ====================
  const handleCreateSubmit = async (e) => {
    e.preventDefault();
    setLoading(prev => ({ ...prev, action: true }));
    
    try {
      const response = await apiClient.requests.create(createForm);
      
      if (response.request) {
        toast.success(response.message || 'Request created successfully');
        closeModal('create');
        await loadRequests();
        await loadStats();
        if (permissions.isEmployee) {
          await checkPendingRequests();
        }
      }
    } catch (error) {
      console.error('Error creating request:', error);
      
      // Handle validation errors
      if (error.response?.data?.details) {
        setFormErrors(error.response.data.details);
        toast.error('Please check the form for errors');
      } else {
        toast.error(error.response?.data?.detail || error.message || 'Failed to create request');
      }
    } finally {
      setLoading(prev => ({ ...prev, action: false }));
    }
  };

  const handleUpdateSubmit = async (e) => {
    e.preventDefault();
    if (!selectedRequest) return;
    
    setLoading(prev => ({ ...prev, action: true }));
    
    try {
      const response = await apiClient.requests.update(selectedRequest.id, updateForm);
      
      if (response.request) {
        toast.success(response.message || 'Request updated successfully');
        closeModal('update');
        await loadRequests();
        await loadStats();
      }
    } catch (error) {
      console.error('Error updating request:', error);
      
      if (error.response?.data?.details) {
        setFormErrors(error.response.data.details);
        toast.error('Please check the form for errors');
      } else {
        toast.error(error.response?.data?.detail || error.message || 'Failed to update request');
      }
    } finally {
      setLoading(prev => ({ ...prev, action: false }));
    }
  };

  const handleApprove = async () => {
    if (!selectedRequestForAction) return;
    
    setLoading(prev => ({ ...prev, action: true }));
    
    try {
      const response = await apiClient.requests.approve(
        selectedRequestForAction.id, 
        actionForm.notes
      );
      
      toast.success(response.message || 'Request approved successfully');
      closeModal('approve');
      await loadRequests();
      await loadStats();
    } catch (error) {
      console.error('Error approving request:', error);
      toast.error(error.response?.data?.detail || error.message || 'Failed to approve request');
    } finally {
      setLoading(prev => ({ ...prev, action: false }));
    }
  };

  const handleReject = async () => {
    if (!selectedRequestForAction) return;
    
    setLoading(prev => ({ ...prev, action: true }));
    
    try {
      const response = await apiClient.requests.reject(
        selectedRequestForAction.id, 
        actionForm.notes
      );
      
      toast.success(response.message || 'Request rejected successfully');
      closeModal('reject');
      await loadRequests();
      await loadStats();
    } catch (error) {
      console.error('Error rejecting request:', error);
      toast.error(error.response?.data?.detail || error.message || 'Failed to reject request');
    } finally {
      setLoading(prev => ({ ...prev, action: false }));
    }
  };

  const handleCancel = async () => {
    if (!selectedRequestForAction) return;
    
    setLoading(prev => ({ ...prev, action: true }));
    
    try {
      const response = await apiClient.requests.cancel(
        selectedRequestForAction.id, 
        actionForm.reason
      );
      
      toast.success(response.message || 'Request cancelled successfully');
      closeModal('cancel');
      await loadRequests();
      await loadStats();
      if (permissions.isEmployee) {
        await checkPendingRequests();
      }
    } catch (error) {
      console.error('Error cancelling request:', error);
      toast.error(error.response?.data?.detail || error.message || 'Failed to cancel request');
    } finally {
      setLoading(prev => ({ ...prev, action: false }));
    }
  };

  const handleDelete = async () => {
    if (!selectedRequestForAction) return;
    
    setLoading(prev => ({ ...prev, action: true }));
    
    try {
      const response = await apiClient.requests.delete(selectedRequestForAction.id);
      
      toast.success(response.message || 'Request deleted successfully');
      closeModal('delete');
      await loadRequests();
      await loadStats();
      if (permissions.isEmployee) {
        await checkPendingRequests();
      }
    } catch (error) {
      console.error('Error deleting request:', error);
      toast.error(error.response?.data?.detail || error.message || 'Failed to delete request');
    } finally {
      setLoading(prev => ({ ...prev, action: false }));
    }
  };

  const refreshData = async () => {
    setLoading(prev => ({ ...prev, action: true }));
    try {
      await loadRequests();
      if (permissions.canViewAll) {
        await loadStats();
      }
      if (permissions.isEmployee) {
        await checkPendingRequests();
      }
      toast.success('Data refreshed');
    } catch (error) {
      toast.error('Failed to refresh data');
    } finally {
      setLoading(prev => ({ ...prev, action: false }));
    }
  };

  // ==================== COMPONENTS ====================
  const StatCard = ({ title, value, icon: Icon, color }) => (
    <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  );

  const StatusBadge = ({ status }) => {
    const Icon = getStatusIcon(status);
    return (
      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium ${getStatusColor(status)}`}>
        <Icon className="w-3 h-3 mr-1" />
        {status?.charAt(0).toUpperCase() + status?.slice(1)}
      </span>
    );
  };

  // ==================== RENDER ====================
  if (loading.initial) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
        <span className="ml-2 text-gray-600">Loading day-off requests...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ==================== HEADER ==================== */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Day-Off Change Requests</h1>
          <p className="text-gray-600 mt-1">
            {permissions.isAdmin && 'Manage all day-off change requests'}
            {permissions.isManager && 'Review and manage team day-off requests'}
            {permissions.isAnalyst && 'View day-off request statistics and details'}
            {permissions.isEmployee && 'Request and manage your day-off changes'}
          </p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={refreshData}
            disabled={loading.action}
            className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 flex items-center"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading.action ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          
          {permissions.canCreate && (
            <button
              onClick={() => openModal('create')}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center"
            >
              <Plus className="w-4 h-4 mr-2" />
              New Request
            </button>
          )}
        </div>
      </div>

      {/* ==================== PENDING REQUESTS ALERT (For Employees) ==================== */}
      {permissions.isEmployee && pendingRequests.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <h3 className="text-sm font-semibold text-yellow-800 mb-1">
                You have {pendingRequests.length} pending request{pendingRequests.length > 1 ? 's' : ''}
              </h3>
              <p className="text-sm text-yellow-700">
                Please wait for your pending request{pendingRequests.length > 1 ? 's' : ''} to be processed before creating a new one.
              </p>
              <div className="mt-2 space-y-1">
                {pendingRequests.map(req => (
                  <div key={req.id} className="text-xs text-yellow-600">
                    • Request to change day off to <span className="font-medium">{getDayLabel(req.requested_day_off)}</span> (Created: {formatDate(req.created_at)})
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ==================== STATISTICS CARDS ==================== */}
      {permissions.canViewAll && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <StatCard title="Total Requests" value={stats.total} icon={FileText} color="bg-blue-600" />
          <StatCard title="Pending" value={stats.pending} icon={Clock} color="bg-yellow-600" />
          <StatCard title="Approved" value={stats.approved} icon={CheckCircle} color="bg-green-600" />
          <StatCard title="Rejected" value={stats.rejected} icon={XCircle} color="bg-red-600" />
          <StatCard title="Cancelled" value={stats.cancelled} icon={Ban} color="bg-gray-600" />
        </div>
      )}

      {/* ==================== FILTERS ==================== */}
      <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder={permissions.canViewAll ? "Search by employee name or reason..." : "Search by reason..."}
                value={filters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                className="w-full pl-10 p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>
          </div>
          
          <select
            value={filters.status}
            onChange={(e) => handleFilterChange('status', e.target.value)}
            className="p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          >
            <option value="all">All Status</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="cancelled">Cancelled</option>
          </select>
          
          {permissions.canViewAll && users.length > 0 && (
            <select
              value={filters.user_id}
              onChange={(e) => handleFilterChange('user_id', e.target.value)}
              className="p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value="">All Employees</option>
              {users.map(user => (
                <option key={user.id} value={user.id}>
                  {user.full_name}
                </option>
              ))}
            </select>
          )}
          
          <button
            onClick={applyFilters}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            Apply Filters
          </button>
          
          <button
            onClick={resetFilters}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Reset
          </button>
        </div>
      </div>

      {/* ==================== REQUESTS TABLE ==================== */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                {permissions.canViewAll && (
                  <th 
                    className="text-left p-4 text-sm font-semibold text-gray-900 cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('user_name')}
                  >
                    <div className="flex items-center gap-1">
                      Employee
                      <ArrowUpDown className="w-4 h-4" />
                    </div>
                  </th>
                )}
                <th className="text-left p-4 text-sm font-semibold text-gray-900">Current Day</th>
                <th className="text-left p-4 text-sm font-semibold text-gray-900">Requested Day</th>
                <th 
                  className="text-left p-4 text-sm font-semibold text-gray-900 cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('effective_from')}
                >
                  <div className="flex items-center gap-1">
                    Effective From
                    <ArrowUpDown className="w-4 h-4" />
                  </div>
                </th>
                <th 
                  className="text-left p-4 text-sm font-semibold text-gray-900 cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('status')}
                >
                  <div className="flex items-center gap-1">
                    Status
                    <ArrowUpDown className="w-4 h-4" />
                  </div>
                </th>
                <th className="text-left p-4 text-sm font-semibold text-gray-900">Actions</th>
              </tr>
            </thead>
            <tbody>
              {paginatedRequests.length === 0 ? (
                <tr>
                  <td colSpan={permissions.canViewAll ? 6 : 5} className="p-8 text-center text-gray-500">
                    No day-off change requests found
                  </td>
                </tr>
              ) : (
                paginatedRequests.map((request) => (
                  <tr key={request.id} className="border-b border-gray-100 hover:bg-gray-50">
                    {permissions.canViewAll && (
                      <td className="p-4">
                        <div className="flex items-center">
                          <div className="w-8 h-8 bg-indigo-100 rounded-full flex items-center justify-center">
                            <User className="w-4 h-4 text-indigo-600" />
                          </div>
                          <div className="ml-3">
                            <p className="text-sm font-medium text-gray-900">
                              {request.user_name || 'Unknown'}
                            </p>
                            <p className="text-xs text-gray-500">
                              {request.user_email || ''}
                            </p>
                          </div>
                        </div>
                      </td>
                    )}
                    <td className="p-4">
                      <span className="text-sm text-gray-900">
                        {getDayLabel(request.current_day_off)}
                      </span>
                    </td>
                    <td className="p-4">
                      <span className="text-sm font-medium text-gray-900">
                        {getDayLabel(request.requested_day_off)}
                      </span>
                    </td>
                    <td className="p-4">
                      <div className="text-sm">
                        <div className="text-gray-900">{formatDate(request.effective_from)}</div>
                        {request.days_until_effective !== null && (
                          <div className="text-xs text-gray-500">
                            {request.days_until_effective > 0 
                              ? `In ${request.days_until_effective} days`
                              : request.days_until_effective === 0
                              ? 'Today'
                              : `${Math.abs(request.days_until_effective)} days ago`}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="p-4">
                      <StatusBadge status={request.status} />
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => openModal('details', request)}
                          className="p-2 hover:bg-gray-100 rounded-lg text-gray-600 hover:text-gray-900"
                          title="View Details"
                        >
                          <Eye className="w-4 h-4" />
                        </button>

                        {/* Employee actions for own pending requests */}
                        {permissions.isEmployee && 
                         request.user_details?.id === user?.id && 
                         request.status === REQUEST_STATUSES.PENDING && (
                          <>
                            <button
                              onClick={() => openModal('cancel', request)}
                              className="p-2 hover:bg-orange-50 rounded-lg text-orange-600 hover:text-orange-700"
                              title="Cancel Request"
                            >
                              <Ban className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => openModal('delete', request)}
                              className="p-2 hover:bg-red-50 rounded-lg text-red-600 hover:text-red-700"
                              title="Delete Request"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </>
                        )}

                        {/* Employee can delete own cancelled requests */}
                        {permissions.isEmployee && 
                         request.user_details?.id === user?.id && 
                         request.status === REQUEST_STATUSES.CANCELLED && (
                          <button
                            onClick={() => openModal('delete', request)}
                            className="p-2 hover:bg-red-50 rounded-lg text-red-600 hover:text-red-700"
                            title="Delete Request"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}

                        {/* Manager/Admin actions for pending requests */}
                        {permissions.canApproveReject && 
                         request.status === REQUEST_STATUSES.PENDING && (
                          <>
                            <button
                              onClick={() => openModal('approve', request)}
                              className="p-2 hover:bg-green-50 rounded-lg text-green-600 hover:text-green-700"
                              title="Approve Request"
                            >
                              <ThumbsUp className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => openModal('reject', request)}
                              className="p-2 hover:bg-red-50 rounded-lg text-red-600 hover:text-red-700"
                              title="Reject Request"
                            >
                              <ThumbsDown className="w-4 h-4" />
                            </button>
                          </>
                        )}

                        {/* Admin/Manager can delete any pending/cancelled requests */}
                        {permissions.canDeleteAny && 
                         (request.status === REQUEST_STATUSES.PENDING || 
                          request.status === REQUEST_STATUSES.CANCELLED) && (
                          <button
                            onClick={() => openModal('delete', request)}
                            className="p-2 hover:bg-red-50 rounded-lg text-red-600 hover:text-red-700"
                            title="Delete Request"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {filteredRequests.length > 0 && (
          <div className="flex items-center justify-between p-4 border-t border-gray-200 bg-gray-50">
            <div className="text-sm text-gray-600">
              Showing {(pagination.currentPage - 1) * pagination.rowsPerPage + 1} to{' '}
              {Math.min(pagination.currentPage * pagination.rowsPerPage, filteredRequests.length)} of{' '}
              {filteredRequests.length} results
            </div>
            
            <div className="flex items-center gap-2">
              <button
                onClick={() => handlePageChange(pagination.currentPage - 1)}
                disabled={pagination.currentPage === 1}
                className="p-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              
              {Array.from({ length: Math.min(5, Math.ceil(filteredRequests.length / pagination.rowsPerPage)) }, (_, i) => {
                let pageNum;
                const totalPages = Math.ceil(filteredRequests.length / pagination.rowsPerPage);
                
                if (totalPages <= 5) {
                  pageNum = i + 1;
                } else if (pagination.currentPage <= 3) {
                  pageNum = i + 1;
                } else if (pagination.currentPage >= totalPages - 2) {
                  pageNum = totalPages - 4 + i;
                } else {
                  pageNum = pagination.currentPage - 2 + i;
                }
                
                return (
                  <button
                    key={pageNum}
                    onClick={() => handlePageChange(pageNum)}
                    className={`w-10 h-10 rounded-lg ${
                      pagination.currentPage === pageNum
                        ? 'bg-indigo-600 text-white'
                        : 'border border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    {pageNum}
                  </button>
                );
              })}
              
              <button
                onClick={() => handlePageChange(pagination.currentPage + 1)}
                disabled={pagination.currentPage === Math.ceil(filteredRequests.length / pagination.rowsPerPage)}
                className="p-2 border border-gray-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ==================== PENDING WARNING MODAL ==================== */}
      {modals.pendingWarning && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full">
            <div className="p-6">
              <div className="flex items-center justify-center w-12 h-12 mx-auto bg-yellow-100 rounded-full mb-4">
                <AlertCircle className="w-6 h-6 text-yellow-600" />
              </div>
              
              <h2 className="text-lg font-semibold text-gray-900 text-center mb-2">
                Pending Request{pendingRequests.length > 1 ? 's' : ''} Exists
              </h2>
              <p className="text-sm text-gray-600 text-center mb-6">
                You have {pendingRequests.length} pending day-off change request{pendingRequests.length > 1 ? 's' : ''}. 
                Please wait for {pendingRequests.length > 1 ? 'them' : 'it'} to be processed before creating a new one.
              </p>
              
              <div className="bg-gray-50 p-4 rounded-lg mb-6 max-h-60 overflow-y-auto">
                <p className="text-sm font-medium text-gray-700 mb-3">Your Pending Requests:</p>
                <div className="space-y-3">
                  {pendingRequests.map((req) => (
                    <div key={req.id} className="bg-white p-3 rounded border border-gray-200">
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">
                            {getDayLabel(req.current_day_off)} → {getDayLabel(req.requested_day_off)}
                          </p>
                          <p className="text-xs text-gray-500 mt-1">
                            Effective from: {formatDate(req.effective_from)}
                          </p>
                        </div>
                        <StatusBadge status={req.status} />
                      </div>
                      <p className="text-xs text-gray-600 line-clamp-2">{req.reason}</p>
                      <p className="text-xs text-gray-400 mt-2">Created: {formatDate(req.created_at)}</p>
                    </div>
                  ))}
                </div>
              </div>
              
              <button
                onClick={() => closeModal('pendingWarning')}
                className="w-full px-4 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
              >
                Understood
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ==================== CREATE REQUEST MODAL ==================== */}
      {modals.create && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900">Request Day-Off Change</h2>
                <button
                  onClick={() => closeModal('create')}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <form onSubmit={handleCreateSubmit} className="space-y-4">
                {/* Current Day Off Display */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                  <div className="flex items-start gap-3">
                    <Calendar className="w-5 h-5 text-blue-600 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-blue-800">Your Current Day Off</p>
                      <p className="text-lg font-semibold text-blue-900">{getDayLabel(user?.day_off || 'none')}</p>
                    </div>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Requested Day Off *
                  </label>
                  <select
                    value={createForm.requested_day_off}
                    onChange={(e) => setCreateForm({ ...createForm, requested_day_off: e.target.value })}
                    className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent ${
                      formErrors.requested_day_off ? 'border-red-500' : 'border-gray-300'
                    }`}
                    required
                  >
                    <option value="">Select a day</option>
                    {DAY_CHOICES.filter(day => day.value !== (user?.day_off || 'none')).map(day => (
                      <option key={day.value} value={day.value}>
                        {day.label}
                      </option>
                    ))}
                  </select>
                  {formErrors.requested_day_off && (
                    <p className="mt-1 text-sm text-red-600">{formErrors.requested_day_off}</p>
                  )}
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Effective From *
                  </label>
                  <input
                    type="date"
                    value={createForm.effective_from}
                    onChange={(e) => setCreateForm({ ...createForm, effective_from: e.target.value })}
                    min={new Date().toISOString().split('T')[0]}
                    className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent ${
                      formErrors.effective_from ? 'border-red-500' : 'border-gray-300'
                    }`}
                    required
                  />
                  {formErrors.effective_from && (
                    <p className="mt-1 text-sm text-red-600">{formErrors.effective_from}</p>
                  )}
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Reason for Change *
                  </label>
                  <textarea
                    value={createForm.reason}
                    onChange={(e) => setCreateForm({ ...createForm, reason: e.target.value })}
                    rows={4}
                    className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent ${
                      formErrors.reason ? 'border-red-500' : 'border-gray-300'
                    }`}
                    placeholder="Please explain why you need this change..."
                    required
                  />
                  {formErrors.reason && (
                    <p className="mt-1 text-sm text-red-600">{formErrors.reason}</p>
                  )}
                </div>
                
                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => closeModal('create')}
                    className="flex-1 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
                    disabled={loading.action}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading.action}
                    className="flex-1 px-4 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 flex items-center justify-center"
                  >
                    {loading.action ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      'Create Request'
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* ==================== REQUEST DETAILS MODAL ==================== */}
      {modals.details && selectedRequest && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-semibold text-gray-900">Request Details</h2>
                <button
                  onClick={() => closeModal('details')}
                  className="p-2 hover:bg-gray-100 rounded-lg"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              
              <div className="space-y-6">
                {/* Status */}
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-600">Status</span>
                  <StatusBadge status={selectedRequest.status} />
                </div>
                
                {/* Employee Info - Show for admin/manager/analyst ONLY */}
                {permissions.canViewEmployeeDetails && selectedRequest.user_details && (
                  <div className="border-t border-gray-200 pt-4">
                    <h3 className="text-sm font-medium text-gray-700 mb-3">Employee Information</h3>
                    <div className="bg-gray-50 p-4 rounded-lg space-y-3">
                      <div className="flex items-center">
                        <UserCircle className="w-5 h-5 text-gray-400 mr-2" />
                        <div>
                          <p className="text-sm font-medium text-gray-900">{selectedRequest.user_details.full_name}</p>
                          <p className="text-xs text-gray-500">Full Name</p>
                        </div>
                      </div>
                      <div className="flex items-center">
                        <AtSign className="w-5 h-5 text-gray-400 mr-2" />
                        <div>
                          <p className="text-sm text-gray-900">{selectedRequest.user_details.email}</p>
                          <p className="text-xs text-gray-500">Email</p>
                        </div>
                      </div>
                      <div className="flex items-center">
                        <Briefcase className="w-5 h-5 text-gray-400 mr-2" />
                        <div>
                          <p className="text-sm text-gray-900 capitalize">{selectedRequest.user_details.role}</p>
                          <p className="text-xs text-gray-500">Role</p>
                        </div>
                      </div>
                      <div className="flex items-center">
                        <Phone className="w-5 h-5 text-gray-400 mr-2" />
                        <div>
                          <p className="text-sm text-gray-900">{selectedRequest.user_details.phone_number || 'N/A'}</p>
                          <p className="text-xs text-gray-500">Phone</p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                {/* Day Off Change */}
                <div className="border-t border-gray-200 pt-4">
                  <h3 className="text-sm font-medium text-gray-700 mb-3">Day Off Change</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <p className="text-xs text-gray-500 mb-1">Current Day Off</p>
                      <p className="text-sm font-medium text-gray-900">
                        {getDayLabel(selectedRequest.current_day_off)}
                      </p>
                    </div>
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <p className="text-xs text-gray-500 mb-1">Requested Day Off</p>
                      <p className="text-sm font-medium text-gray-900">
                        {getDayLabel(selectedRequest.requested_day_off)}
                      </p>
                    </div>
                  </div>
                </div>
                
                {/* Effective Date */}
                <div className="border-t border-gray-200 pt-4">
                  <h3 className="text-sm font-medium text-gray-700 mb-3">Effective Date</h3>
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-sm text-gray-900">{formatDate(selectedRequest.effective_from)}</p>
                    {selectedRequest.days_until_effective !== null && (
                      <p className="text-xs text-gray-500 mt-1">
                        {selectedRequest.days_until_effective > 0 
                          ? `Takes effect in ${selectedRequest.days_until_effective} days`
                          : selectedRequest.days_until_effective === 0
                          ? 'Takes effect today'
                          : `Was supposed to take effect ${Math.abs(selectedRequest.days_until_effective)} days ago`}
                      </p>
                    )}
                  </div>
                </div>
                
                {/* Reason - Now in modal instead of table */}
                <div className="border-t border-gray-200 pt-4">
                  <h3 className="text-sm font-medium text-gray-700 mb-3">Reason for Change</h3>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-900 whitespace-pre-wrap">{selectedRequest.reason}</p>
                  </div>
                </div>
                
                {/* Approval/Rejection Info */}
                {(selectedRequest.status === REQUEST_STATUSES.APPROVED || 
                  selectedRequest.status === REQUEST_STATUSES.REJECTED) && (
                  <div className="border-t border-gray-200 pt-4">
                    <h3 className="text-sm font-medium text-gray-700 mb-3">
                      {selectedRequest.status === REQUEST_STATUSES.APPROVED ? 'Approval' : 'Rejection'} Information
                    </h3>
                    <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                      <div className="flex items-center">
                        <User className="w-4 h-4 text-gray-400 mr-2" />
                        <span className="text-sm text-gray-900">
                          {selectedRequest.approved_by?.full_name || 'Unknown'}
                        </span>
                      </div>
                      {selectedRequest.approved_at && (
                        <div className="flex items-center">
                          <Clock className="w-4 h-4 text-gray-400 mr-2" />
                          <span className="text-sm text-gray-600">
                            {formatDateTime(selectedRequest.approved_at)}
                          </span>
                        </div>
                      )}
                      {selectedRequest.approval_notes && (
                        <div className="mt-2 pt-2 border-t border-gray-200">
                          <p className="text-xs text-gray-500 mb-1">Notes:</p>
                          <p className="text-sm text-gray-900">{selectedRequest.approval_notes}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                {/* Cancellation Info */}
                {selectedRequest.status === REQUEST_STATUSES.CANCELLED && (
                  <div className="border-t border-gray-200 pt-4">
                    <h3 className="text-sm font-medium text-gray-700 mb-3">Cancellation Information</h3>
                    <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                      <div className="flex items-center">
                        <User className="w-4 h-4 text-gray-400 mr-2" />
                        <span className="text-sm text-gray-900">
                          {selectedRequest.cancelled_by?.full_name || 'Unknown'}
                        </span>
                      </div>
                      {selectedRequest.cancelled_at && (
                        <div className="flex items-center">
                          <Clock className="w-4 h-4 text-gray-400 mr-2" />
                          <span className="text-sm text-gray-600">
                            {formatDateTime(selectedRequest.cancelled_at)}
                          </span>
                        </div>
                      )}
                      {selectedRequest.cancellation_reason && (
                        <div className="mt-2 pt-2 border-t border-gray-200">
                          <p className="text-xs text-gray-500 mb-1">Reason:</p>
                          <p className="text-sm text-gray-900">{selectedRequest.cancellation_reason}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                
                {/* Timestamps */}
                <div className="border-t border-gray-200 pt-4">
                  <h3 className="text-sm font-medium text-gray-700 mb-3">Timeline</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <p className="text-xs text-gray-500 mb-1">Created</p>
                      <p className="text-sm text-gray-900">{formatDateTime(selectedRequest.created_at)}</p>
                    </div>
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <p className="text-xs text-gray-500 mb-1">Last Updated</p>
                      <p className="text-sm text-gray-900">{formatDateTime(selectedRequest.updated_at)}</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="flex gap-3 pt-6 mt-6 border-t border-gray-200">
                <button
                  onClick={() => closeModal('details')}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Close
                </button>
                
                {/* Employee actions for own pending requests */}
                {permissions.isEmployee && 
                 selectedRequest.user_details?.id === user?.id && 
                 selectedRequest.status === REQUEST_STATUSES.PENDING && (
                  <>
                    <button
                      onClick={() => {
                        closeModal('details');
                        openModal('cancel', selectedRequest);
                      }}
                      className="flex-1 px-4 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700"
                    >
                      Cancel Request
                    </button>
                  </>
                )}
                
                {/* Admin/Manager actions for pending requests */}
                {permissions.canApproveReject && 
                 selectedRequest.status === REQUEST_STATUSES.PENDING && (
                  <>
                    <button
                      onClick={() => {
                        closeModal('details');
                        openModal('approve', selectedRequest);
                      }}
                      className="flex-1 px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => {
                        closeModal('details');
                        openModal('reject', selectedRequest);
                      }}
                      className="flex-1 px-4 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700"
                    >
                      Reject
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ==================== APPROVE REQUEST MODAL ==================== */}
      {modals.approve && selectedRequestForAction && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full">
            <div className="p-6">
              <div className="flex items-center justify-center w-12 h-12 mx-auto bg-green-100 rounded-full mb-4">
                <ThumbsUp className="w-6 h-6 text-green-600" />
              </div>
              
              <h2 className="text-lg font-semibold text-gray-900 text-center mb-2">Approve Request</h2>
              <p className="text-sm text-gray-600 text-center mb-6">
                Are you sure you want to approve this request from{' '}
                <span className="font-medium">{selectedRequestForAction.user_name}</span>?
              </p>
              
              <div className="bg-gray-50 p-4 rounded-lg mb-6">
                <p className="text-sm font-medium text-gray-700 mb-2">Request Details:</p>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Current Day Off:</span>
                    <span className="font-medium text-gray-900">
                      {getDayLabel(selectedRequestForAction.current_day_off)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Requested Day Off:</span>
                    <span className="font-medium text-gray-900">
                      {getDayLabel(selectedRequestForAction.requested_day_off)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Effective From:</span>
                    <span className="font-medium text-gray-900">
                      {formatDate(selectedRequestForAction.effective_from)}
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Approval Notes (Optional)
                </label>
                <textarea
                  value={actionForm.notes}
                  onChange={(e) => setActionForm({ ...actionForm, notes: e.target.value })}
                  rows={3}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent"
                  placeholder="Add any notes about this approval..."
                />
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={() => closeModal('approve')}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
                  disabled={loading.action}
                >
                  Cancel
                </button>
                <button
                  onClick={handleApprove}
                  disabled={loading.action}
                  className="flex-1 px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center justify-center"
                >
                  {loading.action ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    'Approve'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ==================== REJECT REQUEST MODAL ==================== */}
      {modals.reject && selectedRequestForAction && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full">
            <div className="p-6">
              <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full mb-4">
                <ThumbsDown className="w-6 h-6 text-red-600" />
              </div>
              
              <h2 className="text-lg font-semibold text-gray-900 text-center mb-2">Reject Request</h2>
              <p className="text-sm text-gray-600 text-center mb-6">
                Are you sure you want to reject this request from{' '}
                <span className="font-medium">{selectedRequestForAction.user_name}</span>?
              </p>
              
              <div className="bg-gray-50 p-4 rounded-lg mb-6">
                <p className="text-sm font-medium text-gray-700 mb-2">Request Details:</p>
                <div className="space-y-1 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Current Day Off:</span>
                    <span className="font-medium text-gray-900">
                      {getDayLabel(selectedRequestForAction.current_day_off)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Requested Day Off:</span>
                    <span className="font-medium text-gray-900">
                      {getDayLabel(selectedRequestForAction.requested_day_off)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Effective From:</span>
                    <span className="font-medium text-gray-900">
                      {formatDate(selectedRequestForAction.effective_from)}
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Rejection Reason *
                </label>
                <textarea
                  value={actionForm.notes}
                  onChange={(e) => setActionForm({ ...actionForm, notes: e.target.value })}
                  rows={3}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-transparent"
                  placeholder="Please explain why this request is being rejected..."
                  required
                />
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={() => closeModal('reject')}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
                  disabled={loading.action}
                >
                  Cancel
                </button>
                <button
                  onClick={handleReject}
                  disabled={loading.action || !actionForm.notes}
                  className="flex-1 px-4 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center justify-center"
                >
                  {loading.action ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    'Reject'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ==================== CANCEL REQUEST MODAL ==================== */}
      {modals.cancel && selectedRequestForAction && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full">
            <div className="p-6">
              <div className="flex items-center justify-center w-12 h-12 mx-auto bg-orange-100 rounded-full mb-4">
                <Ban className="w-6 h-6 text-orange-600" />
              </div>
              
              <h2 className="text-lg font-semibold text-gray-900 text-center mb-2">Cancel Request</h2>
              <p className="text-sm text-gray-600 text-center mb-6">
                Are you sure you want to cancel this request?
              </p>
              
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Cancellation Reason (Optional)
                </label>
                <textarea
                  value={actionForm.reason}
                  onChange={(e) => setActionForm({ ...actionForm, reason: e.target.value })}
                  rows={3}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  placeholder="Explain why you're cancelling this request..."
                />
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={() => closeModal('cancel')}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
                  disabled={loading.action}
                >
                  Go Back
                </button>
                <button
                  onClick={handleCancel}
                  disabled={loading.action}
                  className="flex-1 px-4 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 disabled:opacity-50 flex items-center justify-center"
                >
                  {loading.action ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    'Cancel Request'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ==================== DELETE REQUEST MODAL ==================== */}
      {modals.delete && selectedRequestForAction && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full">
            <div className="p-6">
              <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full mb-4">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
              
              <h2 className="text-lg font-semibold text-gray-900 text-center mb-2">Delete Request</h2>
              <p className="text-sm text-gray-600 text-center mb-6">
                Are you sure you want to permanently delete this request?
                <br />
                <span className="text-xs text-gray-500 mt-2 block">This action cannot be undone.</span>
              </p>
              
              <div className="bg-gray-50 p-4 rounded-lg mb-6">
                <p className="text-sm font-medium text-gray-700 mb-2">Request Summary:</p>
                <div className="space-y-1 text-sm">
                  {permissions.canViewAll && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Employee:</span>
                      <span className="font-medium text-gray-900">
                        {selectedRequestForAction.user_name || 'Unknown'}
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-gray-600">Status:</span>
                    <StatusBadge status={selectedRequestForAction.status} />
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Requested Day:</span>
                    <span className="font-medium text-gray-900">
                      {getDayLabel(selectedRequestForAction.requested_day_off)}
                    </span>
                  </div>
                </div>
              </div>
              
              <div className="flex gap-3">
                <button
                  onClick={() => closeModal('delete')}
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg hover:bg-gray-50"
                  disabled={loading.action}
                >
                  Cancel
                </button>
                <button
                  onClick={handleDelete}
                  disabled={loading.action}
                  className="flex-1 px-4 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 flex items-center justify-center"
                >
                  {loading.action ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    'Delete Permanently'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}