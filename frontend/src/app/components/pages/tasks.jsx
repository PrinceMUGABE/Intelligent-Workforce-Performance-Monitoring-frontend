/* eslint-disable react-hooks/exhaustive-deps */
/* eslint-disable no-unused-vars */
import { useState, useEffect, useCallback } from 'react';
import {
  Plus, Edit2, Trash2, Search, Calendar, Clock, User,
  CheckCircle2, Circle, AlertCircle, Filter, Eye,
  ChevronLeft, ChevronRight, Loader2, Download, MoreVertical,
  UserPlus, Users, Building2, Briefcase, X, Play, AlertTriangle,
  ChevronDown, UserCog, RefreshCw
} from 'lucide-react';
import { toast } from 'sonner';
import { useAuth } from '../../context/auth-context';
import { format, parseISO, isValid, differenceInDays } from 'date-fns';

// ==================== CONSTANTS ====================
const ASSIGNMENT_TYPES = {
  SINGLE: 'single',
  MULTIPLE: 'multiple',
  DEPARTMENT: 'department',
  ALL_EMPLOYEES: 'all_employees',
  ALL_USERS: 'all_users',
  ROLE_BASED: 'role_based'
};

const TASK_STATUSES = {
  PENDING: 'pending',
  ACTIVE: 'active',
  NOT_ACTIVE: 'not-active'
};

const ASSIGNMENT_STATUSES = {
  SCHEDULED: 'scheduled',
  ACTIVE: 'active',
  COMPLETED: 'completed',
  MISSED: 'missed',
  REASSIGNED: 'reassigned',
  CANCELLED: 'cancelled'
};

const PRIORITIES = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  URGENT: 'urgent'
};

const USER_ROLES = {
  ADMIN: 'admin',
  MANAGER: 'manager',
  ANALYST: 'analyst',
  EMPLOYEE: 'employee'
};

// ==================== HELPER FUNCTIONS ====================
const formatDateTime = (dateTimeString) => {
  if (!dateTimeString) return 'N/A';
  try {
    const date = parseISO(dateTimeString);
    return isValid(date) ? format(date, 'MMM dd, yyyy HH:mm') : 'Invalid date';
  } catch {
    return 'Invalid date';
  }
};

const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  try {
    const date = parseISO(dateString);
    return isValid(date) ? format(date, 'MMM dd, yyyy') : 'Invalid date';
  } catch {
    return 'Invalid date';
  }
};

const formatTime = (dateTimeString) => {
  if (!dateTimeString) return 'N/A';
  try {
    const date = parseISO(dateTimeString);
    return isValid(date) ? format(date, 'HH:mm') : 'Invalid time';
  } catch {
    return 'Invalid time';
  }
};

const formatDateTimeForInput = (date) => {
  if (!date) return '';
  const d = new Date(date);
  return format(d, "yyyy-MM-dd'T'HH:mm");
};

const getDurationHours = (start, end) => {
  if (!start || !end) return 'N/A';
  try {
    const startDate = parseISO(start);
    const endDate = parseISO(end);
    if (!isValid(startDate) || !isValid(endDate)) return 'N/A';
    const hours = (endDate - startDate) / (1000 * 60 * 60);
    return hours.toFixed(1);
  } catch {
    return 'N/A';
  }
};

const getPriorityColor = (priority) => {
  switch (priority?.toLowerCase()) {
    case 'urgent': return 'bg-red-100 text-red-700';
    case 'high': return 'bg-orange-100 text-orange-700';
    case 'medium': return 'bg-yellow-100 text-yellow-700';
    case 'low': return 'bg-green-100 text-green-700';
    default: return 'bg-slate-100 text-slate-700';
  }
};

const getStatusIcon = (status) => {
  switch (status?.toLowerCase()) {
    case 'completed':
      return <CheckCircle2 className="w-4 h-4 text-green-600" />;
    case 'active':
      return <Circle className="w-4 h-4 text-blue-600" />;
    case 'scheduled':
      return <Calendar className="w-4 h-4 text-purple-600" />;
    case 'missed':
      return <AlertCircle className="w-4 h-4 text-red-600" />;
    case 'cancelled':
    case 'reassigned':
      return <X className="w-4 h-4 text-orange-600" />;
    case 'pending':
      return <Circle className="w-4 h-4 text-yellow-600" />;
    case 'not-active':
      return <Circle className="w-4 h-4 text-slate-400" />;
    default:
      return <Circle className="w-4 h-4 text-slate-400" />;
  }
};

const getStatusBadge = (status) => {
  switch (status?.toLowerCase()) {
    case 'completed':
      return 'bg-green-100 text-green-700';
    case 'active':
      return 'bg-blue-100 text-blue-700';
    case 'scheduled':
      return 'bg-purple-100 text-purple-700';
    case 'missed':
      return 'bg-red-100 text-red-700';
    case 'cancelled':
    case 'reassigned':
      return 'bg-orange-100 text-orange-700';
    case 'pending':
      return 'bg-yellow-100 text-yellow-700';
    case 'not-active':
      return 'bg-slate-100 text-slate-700';
    default:
      return 'bg-slate-100 text-slate-700';
  }
};

// ==================== ROLE PERMISSIONS ====================
const getRolePermissions = (role) => {
  const permissions = {
    // Task permissions
    canViewTasks: false,
    canCreateTasks: false,
    canEditTasks: false,
    canDeleteTasks: false,
    canViewAllTasks: false,

    // Assignment permissions
    canViewAssignments: false,
    canViewAllAssignments: false,
    canCreateAssignments: false,
    canEditAssignments: false,
    canDeleteAssignments: false,
    canBulkAssign: false,
    canAssignToRole: false,
    canManageTemplates: false,
    canManageOverloads: false,

    // Employee actions
    canStartTasks: false,
    canCompleteTasks: false,
    canViewOwnAssignments: false,

    // Data access
    canViewAllDepartments: false,
    canViewAllEmployees: false,
    canViewAllUsers: false,

    // UI visibility
    showTaskStats: false,
    showAssignmentStats: false,
    showFilters: false,
    showExport: false,

    description: ''
  };

  switch (role) {
    case USER_ROLES.ADMIN:
      return {
        ...permissions,
        canViewTasks: true,
        canCreateTasks: true,
        canEditTasks: true,
        canDeleteTasks: true,
        canViewAllTasks: true,
        canViewAssignments: true,
        canViewAllAssignments: true,
        canCreateAssignments: true,
        canEditAssignments: true,
        canDeleteAssignments: true,
        canBulkAssign: true,
        canAssignToRole: true,
        canManageTemplates: true,
        canManageOverloads: true,
        canViewAllDepartments: true,
        canViewAllEmployees: true,
        canViewAllUsers: true,
        showTaskStats: true,
        showAssignmentStats: true,
        showFilters: true,
        showExport: true,
        description: 'Full system administration - manage tasks, assignments, templates, and all user activities'
      };

    case USER_ROLES.MANAGER:
      return {
        ...permissions,
        canViewTasks: true,
        canCreateTasks: true,
        canEditTasks: true,
        canDeleteTasks: false,
        canViewAllTasks: true,
        canViewAssignments: true,
        canViewAllAssignments: true,
        canCreateAssignments: true,
        canEditAssignments: true,
        canDeleteAssignments: false,
        canBulkAssign: true,
        canAssignToRole: true,
        canManageTemplates: true,
        canManageOverloads: true,
        canViewAllDepartments: true,
        canViewAllEmployees: true,
        canViewAllUsers: false,
        showTaskStats: true,
        showAssignmentStats: true,
        showFilters: true,
        showExport: true,
        description: 'Team management - create and assign tasks, monitor team progress'
      };

    case USER_ROLES.ANALYST:
      return {
        ...permissions,
        canViewTasks: true,
        canCreateTasks: false,
        canEditTasks: false,
        canDeleteTasks: false,
        canViewAllTasks: true,
        canViewAssignments: true,
        canViewAllAssignments: true,
        canCreateAssignments: false,
        canEditAssignments: false,
        canDeleteAssignments: false,
        canBulkAssign: false,
        canAssignToRole: false,
        canManageTemplates: false,
        canManageOverloads: true,
        canViewAllDepartments: true,
        canViewAllEmployees: true,
        canViewAllUsers: false,
        showTaskStats: true,
        showAssignmentStats: true,
        showFilters: true,
        showExport: true,
        description: 'Analytics and monitoring - view all tasks and assignments'
      };

    case USER_ROLES.EMPLOYEE:
      return {
        ...permissions,
        canViewTasks: true,
        canCreateTasks: false,
        canEditTasks: false,
        canDeleteTasks: false,
        canViewAllTasks: false,
        canViewAssignments: true,
        canViewAllAssignments: false,
        canCreateAssignments: false,
        canEditAssignments: false,
        canDeleteAssignments: false,
        canBulkAssign: false,
        canAssignToRole: false,
        canManageTemplates: false,
        canManageOverloads: false,
        canStartTasks: true,
        canCompleteTasks: true,
        canViewOwnAssignments: true,
        canViewAllDepartments: false,
        canViewAllEmployees: false,
        canViewAllUsers: false,
        showTaskStats: false,
        showAssignmentStats: true,
        showFilters: true,
        showExport: false,
        description: 'Manage your assigned tasks and track your progress'
      };

    default:
      return permissions;
  }
};

// ==================== MAIN COMPONENT ====================
export default function TasksPage() {
  const { user, api } = useAuth();
  const permissions = getRolePermissions(user?.role);

  // ==================== STATE MANAGEMENT ====================
  // Loading states
  const [loading, setLoading] = useState({
    initial: true,
    tasks: false,
    assignments: false,
    departments: false,
    employees: false,
    users: false,
    action: false
  });

  // Data states
  const [tasks, setTasks] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [allUsers, setAllUsers] = useState([]);
  const [filteredEmployees, setFilteredEmployees] = useState([]);

  // UI states
  const [activeTab, setActiveTab] = useState('assignments');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const itemsPerPage = 10;

  // Modal states
  const [modals, setModals] = useState({
    task: false,
    assignment: false,
    bulkAssignment: false,
    details: false,
    template: false,
    overload: false
  });

  // Selected items
  const [selectedItem, setSelectedItem] = useState(null);
  const [selectedItemType, setSelectedItemType] = useState(null);
  const [editingTask, setEditingTask] = useState(null);
  const [editingAssignment, setEditingAssignment] = useState(null);
  const [selectedEmployees, setSelectedEmployees] = useState([]);
  const [bulkAssignmentResult, setBulkAssignmentResult] = useState(null);

  const [statusUpdateResponse, setStatusUpdateResponse] = useState({
    show: false,
    data: null,
    loading: false,
    error: null
  });

  // Filters
  const [filters, setFilters] = useState({
    search: '',
    status: 'all',
    priority: 'all',
    department: 'all',
    dateRange: { start: '', end: '' }
  });

  // ==================== FORM STATES ====================
  // Task form
  const [taskForm, setTaskForm] = useState({
    name: '',
    description: '',
    status: TASK_STATUSES.PENDING
  });

  // Assignment form (single)
  const [assignmentForm, setAssignmentForm] = useState({
    user_id: '',
    task_id: '',
    department_id: '',
    assignment_date: '',
    start_time: '',
    end_time: '',
    priority: PRIORITIES.MEDIUM,
    notes: ''
  });

  // Bulk assignment form
  const [bulkForm, setBulkForm] = useState({
    assignmentType: ASSIGNMENT_TYPES.SINGLE,
    task_id: '',
    role: '',
    department_id: '',
    user_ids: [],
    exclude_user_ids: [],
    assignment_date: '',
    start_time: '',
    end_time: '',
    priority: PRIORITIES.MEDIUM,
    notes: ''
  });

  // ==================== API CLIENT WRAPPER ====================
  const apiClient = {
    get: async (endpoint, params = {}) => {
      try {
        const response = await api.get(endpoint, { params });
        return { data: response.data };
      } catch (error) {
        console.error(`GET ${endpoint} failed:`, error);
        throw error;
      }
    },

    post: async (endpoint, data) => {
      try {
        const response = await api.post(endpoint, data);
        return { data: response.data };
      } catch (error) {
        console.error(`POST ${endpoint} failed:`, error);
        throw error;
      }
    },

    put: async (endpoint, data) => {
      try {
        const response = await api.put(endpoint, data);
        return { data: response.data };
      } catch (error) {
        console.error(`PUT ${endpoint} failed:`, error);
        throw error;
      }
    },

    patch: async (endpoint, data) => {
      try {
        const response = await api.patch(endpoint, data);
        return { data: response.data };
      } catch (error) {
        console.error(`PATCH ${endpoint} failed:`, error);
        throw error;
      }
    },

    delete: async (endpoint) => {
      try {
        const response = await api.delete(endpoint);
        return { data: response.data };
      } catch (error) {
        console.error(`DELETE ${endpoint} failed:`, error);
        throw error;
      }
    },
  };

  // ==================== INITIALIZATION ====================
  useEffect(() => {
    if (user) {
      initializeData();
    }
  }, [user?.role]);

  const initializeData = async () => {
    if (!user) {
      setLoading(prev => ({ ...prev, initial: false }));
      return;
    }

    setLoading(prev => ({ ...prev, initial: true }));

    try {
      await fetchDepartments();

      if (permissions.canViewTasks) {
        await fetchTasks();
      }

      if (permissions.canViewAssignments) {
        await fetchAssignments();
      }

      if (permissions.canViewAllEmployees) {
        await fetchAllEmployees();
      }

      if (permissions.canViewAllUsers) {
        await fetchAllUsers();
      }

    } catch (error) {
      console.error('Error initializing data:', error);

      if (error.response?.status === 401) {
        toast.error('Session expired. Please login again.');
      } else {
        toast.error('Failed to load initial data');
      }
    } finally {
      setLoading(prev => ({ ...prev, initial: false }));
    }
  };

  // ==================== API CALLS - DEPARTMENTS ====================
  const fetchDepartments = async () => {
    setLoading(prev => ({ ...prev, departments: true }));
    try {
      const response = await apiClient.get('/departments/all/');
      setDepartments(response.data?.data || []);
    } catch (error) {
      console.error('Error fetching departments:', error);
      if (error.response?.status !== 401) {
        toast.error('Failed to load departments');
      }
    } finally {
      setLoading(prev => ({ ...prev, departments: false }));
    }
  };

  // ==================== API CALLS - EMPLOYEES ====================
  const fetchEmployeesByDepartment = async (departmentId) => {
    if (!departmentId) {
      setFilteredEmployees([]);
      return [];
    }

    setLoading(prev => ({ ...prev, employees: true }));
    try {
      const response = await apiClient.get(`/departments/${departmentId}/employees/`);
      const employeesData = response.data?.data || [];
      setFilteredEmployees(employeesData);
      return employeesData;
    } catch (error) {
      console.error('Error fetching department employees:', error);
      if (error.response?.status !== 401) {
        toast.error('Failed to load department employees');
      }
      setFilteredEmployees([]);
      return [];
    } finally {
      setLoading(prev => ({ ...prev, employees: false }));
    }
  };

  const fetchAllEmployees = async () => {
    setLoading(prev => ({ ...prev, employees: true }));
    try {
      const response = await apiClient.get('/users/', {
        role: USER_ROLES.EMPLOYEE
      });
      setEmployees(response.data?.data || []);
    } catch (error) {
      console.error('Error fetching employees:', error);
      if (error.response?.status !== 401) {
        toast.error('Failed to load employees');
      }
    } finally {
      setLoading(prev => ({ ...prev, employees: false }));
    }
  };

  const fetchAllUsers = async () => {
    setLoading(prev => ({ ...prev, users: true }));
    try {
      const response = await apiClient.get('/users/');
      setAllUsers(response.data?.data || []);
    } catch (error) {
      console.error('Error fetching users:', error);
      if (error.response?.status !== 401) {
        toast.error('Failed to load users');
      }
    } finally {
      setLoading(prev => ({ ...prev, users: false }));
    }
  };

  // ==================== API CALLS - TASKS ====================
  const fetchTasks = async (page = currentPage, customFilters = {}) => {
    if (!permissions.canViewTasks || !user) return;

    setLoading(prev => ({ ...prev, tasks: true }));
    try {
      const params = {
        page,
        limit: itemsPerPage,
        ...customFilters
      };

      if (filters.search) params.search = filters.search;
      if (filters.status !== 'all') params.status = filters.status;

      let response;

      if (user?.role === USER_ROLES.EMPLOYEE && !permissions.canViewAllTasks) {
        const myAssignments = await fetchMyAssignments();
        const taskIds = myAssignments
          .map(a => a.task?.id || a.task_details?.id)
          .filter(Boolean);

        if (taskIds.length === 0) {
          setTasks([]);
          setTotalItems(0);
          setTotalPages(1);
          return;
        }

        response = await apiClient.get('/task/all/', {
          ...params,
          id__in: taskIds.join(',')
        });
      } else {
        response = await apiClient.get('/task/all/', params);
      }

      if (response.data) {
        setTasks(response.data.data || response.data || []);
        setTotalItems(response.data.count || response.data.length || 0);
        setTotalPages(Math.ceil((response.data.count || response.data.length || 0) / itemsPerPage));
      }

    } catch (error) {
      console.error('Error fetching tasks:', error);
      if (error.response?.status !== 401) {
        toast.error('Failed to load tasks');
      }
    } finally {
      setLoading(prev => ({ ...prev, tasks: false }));
    }
  };

  const fetchMyAssignments = async () => {
    try {
      const response = await apiClient.get('/task-assignments/my-assignments/');
      return response.data?.assignments || [];
    } catch (error) {
      console.error('Error fetching my assignments:', error);
      return [];
    }
  };

  const createTask = async (taskData) => {
    if (!permissions.canCreateTasks) {
      toast.error('You do not have permission to create tasks');
      return;
    }

    setLoading(prev => ({ ...prev, action: true }));
    try {
      const response = await apiClient.post('/task/create/', taskData);
      toast.success('Task created successfully!');
      fetchTasks();
      closeModal('task');
      return response.data;
    } catch (error) {
      console.error('Error creating task:', error);

      if (error.response?.data) {
        const errorData = error.response.data;
        if (errorData.name) {
          toast.error(`Name: ${errorData.name.join(', ')}`);
        } else if (errorData.message) {
          toast.error(errorData.message);
        } else if (errorData.error) {
          toast.error(errorData.error);
        } else {
          toast.error('Failed to create task');
        }
      } else {
        toast.error(error.message || 'Failed to create task');
      }
      throw error;
    } finally {
      setLoading(prev => ({ ...prev, action: false }));
    }
  };

  const updateTask = async (taskId, taskData) => {
    if (!permissions.canEditTasks) {
      toast.error('You do not have permission to edit tasks');
      return;
    }

    setLoading(prev => ({ ...prev, action: true }));
    try {
      const response = await apiClient.put(`/task/update/${taskId}/`, taskData);
      toast.success('Task updated successfully!');
      fetchTasks();
      closeModal('task');
      return response.data;
    } catch (error) {
      console.error('Error updating task:', error);

      if (error.response?.data) {
        const errorData = error.response.data;
        if (errorData.message) {
          toast.error(errorData.message);
        } else if (errorData.error) {
          toast.error(errorData.error);
        } else {
          toast.error('Failed to update task');
        }
      } else {
        toast.error(error.message || 'Failed to update task');
      }
      throw error;
    } finally {
      setLoading(prev => ({ ...prev, action: false }));
    }
  };

  const deleteTask = async (taskId) => {
    if (!permissions.canDeleteTasks) {
      toast.error('You do not have permission to delete tasks');
      return;
    }

    if (!window.confirm('Are you sure you want to delete this task?')) {
      return;
    }

    setLoading(prev => ({ ...prev, action: true }));
    try {
      await apiClient.delete(`/task/delete/${taskId}/`);
      toast.success('Task deleted successfully!');
      fetchTasks();
    } catch (error) {
      console.error('Error deleting task:', error);

      if (error.response?.data) {
        const errorData = error.response.data;
        if (errorData.message) {
          toast.error(errorData.message);
        } else if (errorData.error) {
          toast.error(errorData.error);
        } else {
          toast.error('Failed to delete task');
        }
      } else {
        toast.error(error.message || 'Failed to delete task');
      }
    } finally {
      setLoading(prev => ({ ...prev, action: false }));
    }
  };

  // ==================== API CALLS - ASSIGNMENTS ====================
  const fetchAssignments = async (page = currentPage, customFilters = {}) => {
    if (!permissions.canViewAssignments || !user) return;

    setLoading(prev => ({ ...prev, assignments: true }));
    try {
      let endpoint = '';
      const params = {
        page,
        limit: itemsPerPage,
        ...customFilters
      };

      if (filters.search) params.search = filters.search;
      if (filters.status !== 'all') params.status = filters.status;
      if (filters.priority !== 'all') params.priority = filters.priority;
      if (filters.department !== 'all') params.department_id = filters.department;
      if (filters.dateRange.start) params.start_date = filters.dateRange.start;
      if (filters.dateRange.end) params.end_date = filters.dateRange.end;

      if (user?.role === USER_ROLES.EMPLOYEE) {
        endpoint = '/task-assignments/my-assignments/';
      } else if (permissions.canViewAllAssignments) {
        endpoint = '/task-assignments/all/';
      }

      if (!endpoint) {
        setAssignments([]);
        return;
      }

      const response = await apiClient.get(endpoint, params);

      if (response.data) {
        if (response.data.assignments) {
          setAssignments(response.data.assignments);
          setTotalItems(response.data.total_count || 0);
          setTotalPages(response.data.total_pages || Math.ceil((response.data.total_count || 0) / itemsPerPage));
        } else if (response.data.data) {
          setAssignments(response.data.data);
          setTotalItems(response.data.count || 0);
          setTotalPages(Math.ceil((response.data.count || 0) / itemsPerPage));
        } else {
          setAssignments(response.data || []);
          setTotalItems(response.data?.length || 0);
          setTotalPages(Math.ceil((response.data?.length || 0) / itemsPerPage));
        }
      }

    } catch (error) {
      console.error('Error fetching assignments:', error);
      if (error.response?.status !== 401) {
        toast.error('Failed to load assignments');
      }
    } finally {
      setLoading(prev => ({ ...prev, assignments: false }));
    }
  };

  const createAssignment = async (assignmentData) => {
    if (!permissions.canCreateAssignments) {
      toast.error('You do not have permission to create assignments');
      return;
    }

    setLoading(prev => ({ ...prev, action: true }));
    try {
      const response = await apiClient.post('/task-assignments/create/', assignmentData);
      toast.success('Assignment created successfully!');
      fetchAssignments();
      closeModal('assignment');
      return response.data;
    } catch (error) {
      console.error('Error creating assignment:', error);

      if (error.response?.data) {
        const errorData = error.response.data;
        if (errorData.message) {
          toast.error(errorData.message);
        } else if (errorData.error) {
          toast.error(errorData.error);
        } else {
          toast.error('Failed to create assignment');
        }
      } else {
        toast.error(error.message || 'Failed to create assignment');
      }
      throw error;
    } finally {
      setLoading(prev => ({ ...prev, action: false }));
    }
  };

  const updateAssignment = async (assignmentData) => {
    if (!permissions.canEditAssignments) {
      toast.error('You do not have permission to edit assignments');
      return;
    }

    setLoading(prev => ({ ...prev, action: true }));
    try {
      const response = await apiClient.put('/task-assignments/modify/', assignmentData);
      toast.success('Assignment updated successfully!');
      fetchAssignments();
      closeModal('assignment');
      return response.data;
    } catch (error) {
      console.error('Error updating assignment:', error);

      if (error.response?.data) {
        const errorData = error.response.data;
        if (errorData.message) {
          toast.error(errorData.message);
        } else if (errorData.error) {
          toast.error(errorData.error);
        } else {
          toast.error('Failed to update assignment');
        }
      } else {
        toast.error(error.message || 'Failed to update assignment');
      }
      throw error;
    } finally {
      setLoading(prev => ({ ...prev, action: false }));
    }
  };

  const deleteAssignment = async (assignmentId) => {
    if (!permissions.canDeleteAssignments) {
      toast.error('You do not have permission to delete assignments');
      return;
    }

    if (!window.confirm('Are you sure you want to delete this assignment?')) {
      return;
    }

    setLoading(prev => ({ ...prev, action: true }));
    try {
      await apiClient.delete(`/task-assignments/${assignmentId}/delete/`);
      toast.success('Assignment deleted successfully!');
      fetchAssignments();
    } catch (error) {
      console.error('Error deleting assignment:', error);

      if (error.response?.data) {
        const errorData = error.response.data;
        if (errorData.message) {
          toast.error(errorData.message);
        } else if (errorData.error) {
          toast.error(errorData.error);
        } else {
          toast.error('Failed to delete assignment');
        }
      } else {
        toast.error(error.message || 'Failed to delete assignment');
      }
    } finally {
      setLoading(prev => ({ ...prev, action: false }));
    }
  };

  // ==================== API CALLS - EMPLOYEE ACTIONS ====================
  const startAssignment = async (assignmentId) => {
    if (!permissions.canStartTasks) {
      toast.error('You do not have permission to start tasks');
      return;
    }

    setLoading(prev => ({ ...prev, action: true }));
    try {
      await apiClient.post(`/task-assignments/${assignmentId}/start/`, {});
      toast.success('Task started successfully!');
      fetchAssignments();
    } catch (error) {
      console.error('Error starting assignment:', error);

      if (error.response?.data) {
        const errorData = error.response.data;
        if (errorData.message) {
          toast.error(errorData.message);
        } else if (errorData.error) {
          toast.error(errorData.error);
        } else {
          toast.error('Failed to start task');
        }
      } else {
        toast.error(error.message || 'Failed to start task');
      }
    } finally {
      setLoading(prev => ({ ...prev, action: false }));
    }
  };

  const completeAssignment = async (assignmentId) => {
    if (!permissions.canCompleteTasks) {
      toast.error('You do not have permission to complete tasks');
      return;
    }

    setLoading(prev => ({ ...prev, action: true }));
    try {
      await apiClient.post(`/task-assignments/${assignmentId}/complete/`, {});
      toast.success('Task completed successfully!');
      fetchAssignments();
    } catch (error) {
      console.error('Error completing assignment:', error);

      if (error.response?.data) {
        const errorData = error.response.data;
        if (errorData.message) {
          toast.error(errorData.message);
        } else if (errorData.error) {
          toast.error(errorData.error);
        } else {
          toast.error('Failed to complete task');
        }
      } else {
        toast.error(error.message || 'Failed to complete task');
      }
    } finally {
      setLoading(prev => ({ ...prev, action: false }));
    }
  };

  // ==================== API CALLS - BULK OPERATIONS ====================
  const bulkAssignTask = async (data) => {
    if (!permissions.canBulkAssign) {
      toast.error('You do not have permission to bulk assign');
      return;
    }

    setLoading(prev => ({ ...prev, action: true }));
    try {
      let endpoint = '';
      let payload = {};

      switch (data.assignmentType) {
        case ASSIGNMENT_TYPES.SINGLE:
          endpoint = '/task-assignments/create/';
          payload = {
            user_id: parseInt(data.user_ids[0]),
            task_id: parseInt(data.task_id),
            assignment_date: data.assignment_date,
            start_time: data.start_time,
            end_time: data.end_time,
            priority: data.priority,
            notes: data.notes,
            department_id: data.department_id ? parseInt(data.department_id) : null
          };
          break;

        case ASSIGNMENT_TYPES.MULTIPLE:
          endpoint = '/task-assignments/assign-to-users/';
          payload = {
            task_id: parseInt(data.task_id),
            user_ids: data.user_ids.map(id => parseInt(id)),
            assignment_date: data.assignment_date,
            start_time: data.start_time,
            end_time: data.end_time,
            priority: data.priority,
            notes: data.notes
          };
          break;

        case ASSIGNMENT_TYPES.DEPARTMENT:
          endpoint = '/task-assignments/assign-to-department/';
          payload = {
            task_id: parseInt(data.task_id),
            department_id: parseInt(data.department_id),
            assignment_date: data.assignment_date,
            start_time: data.start_time,
            end_time: data.end_time,
            priority: data.priority,
            notes: data.notes,
            exclude_user_ids: data.exclude_user_ids?.map(id => parseInt(id)) || []
          };
          break;

        case ASSIGNMENT_TYPES.ROLE_BASED:
          endpoint = '/task-assignments/assign-to-role/';
          payload = {
            task_id: parseInt(data.task_id),
            role: data.role,
            assignment_date: data.assignment_date,
            start_time: data.start_time,
            end_time: data.end_time,
            priority: data.priority,
            notes: data.notes,
            exclude_user_ids: data.exclude_user_ids?.map(id => parseInt(id)) || []
          };
          break;

        case ASSIGNMENT_TYPES.ALL_EMPLOYEES:
          endpoint = '/task-assignments/bulk-assign/';
          payload = {
            task_id: parseInt(data.task_id),
            assignment_date: data.assignment_date,
            start_time: data.start_time,
            end_time: data.end_time,
            priority: data.priority,
            notes: data.notes,
            assign_to_all_employees: true
          };
          break;

        case ASSIGNMENT_TYPES.ALL_USERS:
          endpoint = '/task-assignments/bulk-assign/';
          payload = {
            task_id: parseInt(data.task_id),
            assignment_date: data.assignment_date,
            start_time: data.start_time,
            end_time: data.end_time,
            priority: data.priority,
            notes: data.notes,
            assign_to_all_users: true
          };
          break;

        default:
          throw new Error('Invalid assignment type');
      }

      const response = await apiClient.post(endpoint, payload);

      if (response.data.success) {
        toast.success(`Successfully created ${response.data.created_count || 0} assignments!`);
        setBulkAssignmentResult({
          created_count: response.data.created_count || 0,
          skipped_count: response.data.skipped_count || 0,
          failed_count: response.data.failed_count || 0,
          created_assignments: response.data.created_assignments || [],
          skipped_assignments: response.data.skipped_assignments || [],
          failed_assignments: response.data.failed_assignments || []
        });

        setTimeout(() => {
          closeModal('bulkAssignment');
          fetchAssignments();
        }, 3000);
      }

      return response.data;

    } catch (error) {
      console.error('Error in bulk assignment:', error);

      if (error.response?.data) {
        const errorData = error.response.data;
        if (errorData.message) {
          toast.error(errorData.message);
        } else if (errorData.error) {
          toast.error(errorData.error);
        } else {
          toast.error(error.message || 'Failed to bulk assign task');
        }
      } else {
        toast.error(error.message || 'Failed to bulk assign task');
      }
      throw error;
    } finally {
      setLoading(prev => ({ ...prev, action: false }));
    }
  };

  // ==================== EVENT HANDLERS ====================
  const openModal = (modalName, data = null) => {
    setModals(prev => ({ ...prev, [modalName]: true }));

    switch (modalName) {
      case 'task':
        if (data) {
          setEditingTask(data);
          setTaskForm({
            name: data.name || '',
            description: data.description || '',
            status: data.status || TASK_STATUSES.PENDING
          });
        } else {
          setEditingTask(null);
          setTaskForm({
            name: '',
            description: '',
            status: TASK_STATUSES.PENDING
          });
        }
        break;

      case 'assignment':
        if (data) {
          setEditingAssignment(data);
          setAssignmentForm({
            user_id: data.user?.id || data.user_details?.id || '',
            task_id: data.task?.id || data.task_details?.id || '',
            department_id: data.department?.id || data.department_details?.id || '',
            assignment_date: data.assignment_date || '',
            start_time: data.start_time ? formatDateTimeForInput(data.start_time) : '',
            end_time: data.end_time ? formatDateTimeForInput(data.end_time) : '',
            priority: data.priority || PRIORITIES.MEDIUM,
            notes: data.notes || ''
          });

          if (data.department?.id || data.department_details?.id) {
            fetchEmployeesByDepartment(data.department?.id || data.department_details?.id);
          }
        } else {
          setEditingAssignment(null);
          setAssignmentForm({
            user_id: '',
            task_id: '',
            department_id: '',
            assignment_date: format(new Date(), 'yyyy-MM-dd'),
            start_time: formatDateTimeForInput(new Date()),
            end_time: formatDateTimeForInput(new Date(Date.now() + 60 * 60 * 1000)),
            priority: PRIORITIES.MEDIUM,
            notes: ''
          });
        }
        break;

      case 'bulkAssignment':
        setBulkAssignmentResult(null);
        setSelectedEmployees([]);
        setBulkForm({
          assignmentType: ASSIGNMENT_TYPES.SINGLE,
          task_id: '',
          role: '',
          department_id: '',
          user_ids: [],
          exclude_user_ids: [],
          assignment_date: format(new Date(), 'yyyy-MM-dd'),
          start_time: formatDateTimeForInput(new Date()),
          end_time: formatDateTimeForInput(new Date(Date.now() + 60 * 60 * 1000)),
          priority: PRIORITIES.MEDIUM,
          notes: ''
        });
        break;

      case 'details':
        setSelectedItem(data.item);
        setSelectedItemType(data.type);
        break;
    }
  };

  const closeModal = (modalName) => {
    setModals(prev => ({ ...prev, [modalName]: false }));

    if (modalName === 'assignment' || modalName === 'bulkAssignment') {
      setFilteredEmployees([]);
      setSelectedEmployees([]);
    }

    if (modalName === 'bulkAssignment') {
      setBulkAssignmentResult(null);
    }

    if (modalName === 'details') {
      setSelectedItem(null);
      setSelectedItemType(null);
    }
  };

  const handleTaskSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingTask) {
        await updateTask(editingTask.id, taskForm);
      } else {
        await createTask(taskForm);
      }
    } catch (error) {
      // Error handled in API calls
    }
  };

  const handleAssignmentSubmit = async (e) => {
    e.preventDefault();

    try {
      // Ensure datetime strings have seconds and proper format
      const formatDateTimeForAPI = (datetimeLocal) => {
        if (!datetimeLocal) return null;

        // If it already ends with Z, return as is
        if (datetimeLocal.endsWith('Z')) return datetimeLocal;

        // Add seconds if missing
        let formatted = datetimeLocal;
        if (formatted.includes('T')) {
          const timePart = formatted.split('T')[1];
          if (timePart.split(':').length === 2) {
            formatted = `${formatted}:00`;
          }
        }

        // Create date and convert to ISO string with Z suffix
        const date = new Date(formatted);
        return date.toISOString();
      };

      const formattedData = {
        ...assignmentForm,
        start_time: formatDateTimeForAPI(assignmentForm.start_time),
        end_time: formatDateTimeForAPI(assignmentForm.end_time),
        user_id: parseInt(assignmentForm.user_id),
        task_id: parseInt(assignmentForm.task_id),
        department_id: assignmentForm.department_id ? parseInt(assignmentForm.department_id) : null
      };

      if (editingAssignment) {
        await updateAssignment({
          assignment_id: editingAssignment.id,
          new_task_id: formattedData.task_id,
          new_start_time: formattedData.start_time,
          new_end_time: formattedData.end_time,
          notes: formattedData.notes,
          reason: 'Modified via admin panel'
        });
      } else {
        await createAssignment(formattedData);
      }
    } catch (error) {
      // Error handled in API calls
    }
  };

  const handleBulkSubmit = async (e) => {
    e.preventDefault();

    const formatDateTimeForAPI = (datetimeLocal) => {
      if (!datetimeLocal) return null;
      if (datetimeLocal.endsWith('Z')) return datetimeLocal;

      let formatted = datetimeLocal;
      if (formatted.includes('T')) {
        const timePart = formatted.split('T')[1];
        if (timePart.split(':').length === 2) {
          formatted = `${formatted}:00`;
        }
      }

      const date = new Date(formatted);
      return date.toISOString();
    };

    const formattedData = {
      ...bulkForm,
      start_time: formatDateTimeForAPI(bulkForm.start_time),
      end_time: formatDateTimeForAPI(bulkForm.end_time),
      task_id: parseInt(bulkForm.task_id),
      department_id: bulkForm.department_id ? parseInt(bulkForm.department_id) : null,
      user_ids: bulkForm.user_ids.map(id => parseInt(id)),
      exclude_user_ids: bulkForm.exclude_user_ids?.map(id => parseInt(id)) || []
    };

    await bulkAssignTask(formattedData);
  };

  const handleBulkDepartmentChange = async (e) => {
    const departmentId = e.target.value;
    setBulkForm(prev => ({
      ...prev,
      department_id: departmentId,
      user_ids: []
    }));
    setSelectedEmployees([]);

    if (departmentId) {
      await fetchEmployeesByDepartment(departmentId);
    } else {
      setFilteredEmployees([]);
    }
  };

  const handleEmployeeSelection = (userId) => {
    setSelectedEmployees(prev => {
      const isSelected = prev.includes(userId);
      const newSelection = isSelected
        ? prev.filter(id => id !== userId)
        : [...prev, userId];

      setBulkForm(prevForm => ({
        ...prevForm,
        user_ids: newSelection
      }));

      return newSelection;
    });
  };

  const handleSelectAllEmployees = () => {
    const allIds = filteredEmployees.map(emp => emp.id);
    setSelectedEmployees(allIds);
    setBulkForm(prev => ({
      ...prev,
      user_ids: allIds
    }));
  };

  const handleClearSelection = () => {
    setSelectedEmployees([]);
    setBulkForm(prev => ({
      ...prev,
      user_ids: []
    }));
  };

  const applyFilters = () => {
    setCurrentPage(1);
    if (activeTab === 'tasks') {
      fetchTasks(1, {});
    } else {
      fetchAssignments(1, {});
    }
  };

  const resetFilters = () => {
    setFilters({
      search: '',
      status: 'all',
      priority: 'all',
      department: 'all',
      dateRange: { start: '', end: '' }
    });
    setCurrentPage(1);

    if (activeTab === 'tasks') {
      fetchTasks(1, {});
    } else {
      fetchAssignments(1, {});
    }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setCurrentPage(1);
    resetFilters();

    if (tab === 'tasks') {
      fetchTasks(1);
    } else {
      fetchAssignments(1);
    }
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
    if (activeTab === 'tasks') {
      fetchTasks(page);
    } else {
      fetchAssignments(page);
    }
  };

  const getPossibleTransitions = async (assignmentId) => {
    try {
      const response = await apiClient.get(`/task-assignments/${assignmentId}/transitions/`);
      return response.data;
    } catch (error) {
      console.error('Error fetching transitions:', error);
      return { possible_transitions: [], context: {} };
    }
  };

  const updateAssignmentStatus = async (assignmentId, newStatus, reason = '') => {
    try {
      // Show loading state in modal
      setStatusUpdateResponse({
        show: true,
        data: null,
        loading: true,
        error: null
      });

      console.log('Sending status update request:', {
        assignment_id: assignmentId,
        new_status: newStatus,
        reason: reason
      });

      const response = await apiClient.post('/task-assignments/update-status/', {
        assignment_id: assignmentId,
        new_status: newStatus,
        reason: reason
      });

      console.log("Response received:", response.data);

      if (response.data && response.data.success === true) {
        // Success case - show response in modal
        setStatusUpdateResponse({
          show: true,
          data: response.data,
          loading: false,
          error: null
        });

        const successMsg = response.data.message || `Status updated to ${newStatus}`;
        toast.success(successMsg);
        await fetchAssignments(); // Refresh the list

        // Auto-close modal after 5 seconds on success
        setTimeout(() => {
          setStatusUpdateResponse(prev => ({ ...prev, show: false }));
        }, 5000);

        return response.data;
      } else {
        // Handle case where response is 200 but success=false
        const errorMsg = response.data?.message || response.data?.error || 'Failed to update status';
        console.error('Status update failed (success=false):', errorMsg);

        // Show error in modal
        setStatusUpdateResponse({
          show: true,
          data: response.data,
          loading: false,
          error: errorMsg
        });

        toast.error(errorMsg);
        throw new Error(errorMsg);
      }

    } catch (error) {
      console.error('Error updating status:', error);

      // Log the full error response if available
      if (error.response) {
        console.error('Error response status:', error.response.status);
        console.error('Error response data:', error.response.data);
        console.error('Error response headers:', error.response.headers);
      } else if (error.request) {
        console.error('Error request:', error.request);
      } else {
        console.error('Error message:', error.message);
      }

      // Extract error message from various possible locations
      let errorMessage = 'Failed to update status';
      let errorData = null;

      if (error.response?.data) {
        errorData = error.response.data;

        // Try different possible error message locations
        if (typeof errorData === 'string') {
          errorMessage = errorData;
        } else if (errorData.message) {
          errorMessage = errorData.message;
        } else if (errorData.error) {
          errorMessage = errorData.error;
        } else if (errorData.detail) {
          errorMessage = errorData.detail;
        } else if (errorData.errors) {
          if (typeof errorData.errors === 'object') {
            // Handle field errors
            const fieldErrors = Object.entries(errorData.errors)
              .map(([field, errors]) => `${field}: ${Array.isArray(errors) ? errors.join(', ') : errors}`)
              .join('; ');
            errorMessage = fieldErrors;
          } else {
            errorMessage = errorData.errors;
          }
        } else if (errorData.non_field_errors) {
          errorMessage = Array.isArray(errorData.non_field_errors)
            ? errorData.non_field_errors.join(', ')
            : errorData.non_field_errors;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }

      console.log('Extracted error message:', errorMessage);

      // Show error in modal
      setStatusUpdateResponse({
        show: true,
        data: errorData,
        loading: false,
        error: errorMessage
      });

      // Show the error message to the user
      toast.error(errorMessage, {
        duration: 5000,
        position: 'top-center',
      });

      throw error;
    }
  };

  const StatusUpdateCell = ({ assignment }) => {
    const [transitions, setTransitions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showDropdown, setShowDropdown] = useState(false);

    useEffect(() => {
      if (showDropdown) {
        setLoading(true);
        getPossibleTransitions(assignment.id).then(data => {
          setTransitions(data.possible_transitions || []);
          setLoading(false);
        });
      }
    }, [showDropdown, assignment.id]);

    if (assignment.status === 'completed' || assignment.status === 'cancelled') {
      return (
        <div className="flex items-center">
          {getStatusIcon(assignment.status)}
          <span className="ml-2 capitalize">{assignment.status}</span>
        </div>
      );
    }

    return (
      <div className="relative">
        <button
          onClick={() => setShowDropdown(!showDropdown)}
          className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-lg hover:bg-slate-200"
        >
          {getStatusIcon(assignment.status)}
          <span className="capitalize">{assignment.status}</span>
          <ChevronDown className="w-4 h-4" />
        </button>

        {showDropdown && (
          <div className="absolute z-10 mt-1 w-48 bg-white rounded-lg shadow-lg border border-slate-200 py-1">
            {loading ? (
              <div className="px-4 py-2 text-sm text-slate-500">Loading...</div>
            ) : transitions.length === 0 ? (
              <div className="px-4 py-2 text-sm text-slate-500">No transitions available</div>
            ) : (
              transitions.map(status => (
                <button
                  key={status}
                  onClick={() => {
                    // You could add a prompt for reason here if needed
                    const reason = window.prompt('Enter reason for status change (optional):', '');
                    updateAssignmentStatus(assignment.id, status, reason || '');
                    setShowDropdown(false);
                  }}
                  className="w-full text-left px-4 py-2 text-sm hover:bg-slate-50 capitalize"
                >
                  {status}
                </button>
              ))
            )}
          </div>
        )}
      </div>
    );
  };

  // ==================== UTILITY FUNCTIONS ====================
  const calculateStats = () => {
    if (activeTab === 'tasks') {
      return {
        total: tasks.length,
        pending: tasks.filter(t => t.status === TASK_STATUSES.PENDING).length,
        active: tasks.filter(t => t.status === TASK_STATUSES.ACTIVE).length,
        notActive: tasks.filter(t => t.status === TASK_STATUSES.NOT_ACTIVE).length
      };
    } else {
      return {
        total: assignments.length,
        scheduled: assignments.filter(a => a.status === ASSIGNMENT_STATUSES.SCHEDULED).length,
        active: assignments.filter(a => a.status === ASSIGNMENT_STATUSES.ACTIVE).length,
        completed: assignments.filter(a => a.status === ASSIGNMENT_STATUSES.COMPLETED).length,
        missed: assignments.filter(a => a.status === ASSIGNMENT_STATUSES.MISSED).length,
        cancelled: assignments.filter(a =>
          a.status === ASSIGNMENT_STATUSES.CANCELLED ||
          a.status === ASSIGNMENT_STATUSES.REASSIGNED
        ).length
      };
    }
  };

  const stats = calculateStats();
  const isAdminOrManager = [USER_ROLES.ADMIN, USER_ROLES.MANAGER].includes(user?.role);
  const isAnalyst = user?.role === USER_ROLES.ANALYST;
  const isEmployee = user?.role === USER_ROLES.EMPLOYEE;

  // ==================== RENDER ====================
  if (loading.initial) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
        <span className="ml-2 text-slate-600">Loading tasks and assignments...</span>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-slate-900 mb-2">Authentication Required</h2>
          <p className="text-slate-600 mb-4">Please login to access tasks and assignments</p>
          <button
            onClick={() => window.location.href = '/login'}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            Go to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ==================== HEADER ==================== */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">Tasks & Assignments</h1>
          <p className="text-slate-600 mt-1">{permissions.description}</p>
        </div>

        <div className="flex items-center gap-3">
          {activeTab === 'tasks' && permissions.canCreateTasks && (
            <button
              onClick={() => openModal('task')}
              className="px-4 py-2 bg-gradient-to-r from-sky-600 to-indigo-600 text-white rounded-lg hover:from-sky-700 hover:to-indigo-700 flex items-center"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Task
            </button>
          )}

          {activeTab === 'assignments' && permissions.canCreateAssignments && (
            <>
              <button
                onClick={() => openModal('assignment')}
                className="px-4 py-2 bg-gradient-to-r from-sky-600 to-indigo-600 text-white rounded-lg hover:from-sky-700 hover:to-indigo-700 flex items-center"
              >
                <UserPlus className="w-4 h-4 mr-2" />
                Assign Task
              </button>

              {permissions.canBulkAssign && (
                <button
                  onClick={() => openModal('bulkAssignment')}
                  className="px-4 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 flex items-center"
                >
                  <Users className="w-4 h-4 mr-2" />
                  Bulk Assign
                </button>
              )}
            </>
          )}

          <button>

          </button>

          {/* {permissions.showExport && (
            <button className="px-4 py-2 border border-slate-300 rounded-lg flex items-center hover:bg-slate-50">
              <Download className="w-4 h-4 mr-2" />
              Export
            </button>
          )} */}
        </div>
      </div>

      {/* ==================== TABS ==================== */}
      <div className="border-b border-slate-200">
        <div className="flex gap-6">
          {permissions.canViewTasks && (
            <button
              onClick={() => handleTabChange('tasks')}
              className={`px-1 py-3 border-b-2 transition-colors ${activeTab === 'tasks'
                ? 'border-indigo-600 text-indigo-600 font-semibold'
                : 'border-transparent text-slate-600 hover:text-slate-900'
                }`}
            >
              Tasks {stats.total > 0 && `(${stats.total})`}
            </button>
          )}

          {permissions.canViewAssignments && (
            <button
              onClick={() => handleTabChange('assignments')}
              className={`px-1 py-3 border-b-2 transition-colors ${activeTab === 'assignments'
                ? 'border-indigo-600 text-indigo-600 font-semibold'
                : 'border-transparent text-slate-600 hover:text-slate-900'
                }`}
            >
              Assignments {stats.total > 0 && `(${stats.total})`}
            </button>
          )}
        </div>
      </div>

      {/* ==================== STATISTICS CARDS ==================== */}
      {permissions.showTaskStats && activeTab === 'tasks' && (
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm text-slate-600 font-medium">Total Tasks</h3>
                <div className="text-3xl font-bold text-slate-900 mt-2">{stats.total}</div>
              </div>
              <div className="p-3 bg-slate-100 rounded-lg">
                <CheckCircle2 className="w-6 h-6 text-slate-600" />
              </div>
            </div>
          </div>

          <div className="bg-yellow-50 p-6 rounded-lg border border-yellow-200 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm text-yellow-700 font-medium">Pending</h3>
                <div className="text-3xl font-bold text-yellow-700 mt-2">{stats.pending}</div>
              </div>
              <div className="p-3 bg-yellow-100 rounded-lg">
                <Circle className="w-6 h-6 text-yellow-600" />
              </div>
            </div>
          </div>

          <div className="bg-blue-50 p-6 rounded-lg border border-blue-200 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm text-blue-700 font-medium">Active</h3>
                <div className="text-3xl font-bold text-blue-700 mt-2">{stats.active}</div>
              </div>
              <div className="p-3 bg-blue-100 rounded-lg">
                <Circle className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="bg-green-50 p-6 rounded-lg border border-green-200 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm text-green-700 font-medium">Not Active</h3>
                <div className="text-3xl font-bold text-green-700 mt-2">{stats.notActive}</div>
              </div>
              <div className="p-3 bg-green-100 rounded-lg">
                <X className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </div>
        </div>
      )}

      {permissions.showAssignmentStats && activeTab === 'assignments' && (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm text-slate-600 font-medium">Total Assignments</h3>
                <div className="text-3xl font-bold text-slate-900 mt-2">{stats.total}</div>
              </div>
              <div className="p-3 bg-slate-100 rounded-lg">
                <CheckCircle2 className="w-6 h-6 text-slate-600" />
              </div>
            </div>
          </div>

          <div className="bg-purple-50 p-6 rounded-lg border border-purple-200 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm text-purple-700 font-medium">Scheduled</h3>
                <div className="text-3xl font-bold text-purple-700 mt-2">{stats.scheduled}</div>
              </div>
              <div className="p-3 bg-purple-100 rounded-lg">
                <Calendar className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </div>

          <div className="bg-blue-50 p-6 rounded-lg border border-blue-200 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm text-blue-700 font-medium">Active</h3>
                <div className="text-3xl font-bold text-blue-700 mt-2">{stats.active}</div>
              </div>
              <div className="p-3 bg-blue-100 rounded-lg">
                <Circle className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="bg-green-50 p-6 rounded-lg border border-green-200 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm text-green-700 font-medium">Completed</h3>
                <div className="text-3xl font-bold text-green-700 mt-2">{stats.completed}</div>
              </div>
              <div className="p-3 bg-green-100 rounded-lg">
                <CheckCircle2 className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </div>

          <div className="bg-red-50 p-6 rounded-lg border border-red-200 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm text-red-700 font-medium">Missed</h3>
                <div className="text-3xl font-bold text-red-700 mt-2">{stats.missed}</div>
              </div>
              <div className="p-3 bg-red-100 rounded-lg">
                <AlertCircle className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </div>

          <div className="bg-orange-50 p-6 rounded-lg border border-orange-200 shadow-sm">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm text-orange-700 font-medium">Cancelled</h3>
                <div className="text-3xl font-bold text-orange-700 mt-2">{stats.cancelled}</div>
              </div>
              <div className="p-3 bg-orange-100 rounded-lg">
                <X className="w-6 h-6 text-orange-600" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ==================== FILTERS ==================== */}
      {permissions.showFilters && activeTab === 'assignments' && (
        <div className="bg-white p-6 rounded-lg border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-slate-900 flex items-center">
              <Filter className="w-5 h-5 mr-2 text-indigo-600" />
              Filters
            </h3>
            <button
              onClick={resetFilters}
              className="text-sm text-slate-600 hover:text-slate-900 flex items-center"
            >
              <RefreshCw className="w-3 h-3 mr-1" />
              Reset all
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-3 h-5 w-5 text-slate-400" />
              <input
                type="text"
                placeholder="Search tasks..."
                value={filters.search}
                onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
                className="w-full pl-10 p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>

            <select
              value={filters.status}
              onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
              className="p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value="all">All Statuses</option>
              <option value="scheduled">Scheduled</option>
              <option value="active">Active</option>
              <option value="completed">Completed</option>
              <option value="missed">Missed</option>
              <option value="cancelled">Cancelled</option>
              <option value="reassigned">Reassigned</option>
            </select>

            <select
              value={filters.priority}
              onChange={(e) => setFilters(prev => ({ ...prev, priority: e.target.value }))}
              className="p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            >
              <option value="all">All Priorities</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="urgent">Urgent</option>
            </select>

            {permissions.canViewAllDepartments && (
              <select
                value={filters.department}
                onChange={(e) => setFilters(prev => ({ ...prev, department: e.target.value }))}
                className="p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              >
                <option value="all">All Departments</option>
                {departments.map(dept => (
                  <option key={dept.id} value={dept.id}>{dept.name}</option>
                ))}
              </select>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">From Date</label>
              <input
                type="date"
                value={filters.dateRange.start}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  dateRange: { ...prev.dateRange, start: e.target.value }
                }))}
                className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">To Date</label>
              <input
                type="date"
                value={filters.dateRange.end}
                onChange={(e) => setFilters(prev => ({
                  ...prev,
                  dateRange: { ...prev.dateRange, end: e.target.value }
                }))}
                className="w-full p-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              />
            </div>
          </div>

          <div className="flex justify-end mt-4">
            <button
              onClick={applyFilters}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 flex items-center"
            >
              <Filter className="w-4 h-4 mr-2" />
              Apply Filters
            </button>
          </div>
        </div>
      )}

      {/* ==================== CONTENT TABLE - TASKS ==================== */}
      {activeTab === 'tasks' && (
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left p-4 text-sm font-semibold text-slate-900">Task</th>
                  <th className="text-left p-4 text-sm font-semibold text-slate-900">Status</th>
                  <th className="text-left p-4 text-sm font-semibold text-slate-900">Created</th>
                  <th className="text-left p-4 text-sm font-semibold text-slate-900">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading.tasks ? (
                  <tr>
                    <td colSpan="4" className="p-8 text-center">
                      <Loader2 className="w-8 h-8 animate-spin text-indigo-600 mx-auto" />
                      <p className="text-slate-600 mt-2">Loading tasks...</p>
                    </td>
                  </tr>
                ) : tasks.length === 0 ? (
                  <tr>
                    <td colSpan="4" className="p-8 text-center text-slate-500">
                      No tasks found
                    </td>
                  </tr>
                ) : (
                  tasks.map((task) => (
                    <tr key={task.id} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="p-4">
                        <div>
                          <h4 className="font-medium text-slate-900">{task.name}</h4>
                          <p className="text-sm text-slate-600 mt-1 line-clamp-2">{task.description}</p>
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center">
                          {getStatusIcon(task.status)}
                          <span className="ml-2 capitalize text-sm">{task.status}</span>
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="text-sm text-slate-600">
                          {formatDate(task.created_at)}
                        </div>
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => openModal('details', { item: task, type: 'task' })}
                            className="p-2 hover:bg-slate-100 rounded-lg text-slate-600 hover:text-slate-900"
                            title="View Details"
                          >
                            <Eye className="w-4 h-4" />
                          </button>

                          {permissions.canEditTasks && (
                            <button
                              onClick={() => openModal('task', task)}
                              className="p-2 hover:bg-sky-50 rounded-lg text-sky-600 hover:text-sky-700"
                              title="Edit"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                          )}

                          {permissions.canDeleteTasks && (
                            <button
                              onClick={() => deleteTask(task.id)}
                              className="p-2 hover:bg-red-50 rounded-lg text-red-600 hover:text-red-700"
                              title="Delete"
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
        </div>
      )}

      {/* ==================== CONTENT TABLE - ASSIGNMENTS ==================== */}
      {activeTab === 'assignments' && (
        <div className="bg-white rounded-lg border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left p-4 text-sm font-semibold text-slate-900">Task</th>
                  <th className="text-left p-4 text-sm font-semibold text-slate-900">Department</th>

                  {(isAdminOrManager || isAnalyst) && (
                    <th className="text-left p-4 text-sm font-semibold text-slate-900">Employee</th>
                  )}

                  {isEmployee && (
                    <th className="text-left p-4 text-sm font-semibold text-slate-900">Assigned By</th>
                  )}

                  <th className="text-left p-4 text-sm font-semibold text-slate-900">Date & Time</th>
                  <th className="text-left p-4 text-sm font-semibold text-slate-900">Duration</th>
                  <th className="text-left p-4 text-sm font-semibold text-slate-900">Status</th>
                  <th className="text-left p-4 text-sm font-semibold text-slate-900">Priority</th>
                  <th className="text-left p-4 text-sm font-semibold text-slate-900">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading.assignments ? (
                  <tr>
                    <td colSpan="8" className="p-8 text-center">
                      <Loader2 className="w-8 h-8 animate-spin text-indigo-600 mx-auto" />
                      <p className="text-slate-600 mt-2">Loading assignments...</p>
                    </td>
                  </tr>
                ) : assignments.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="p-8 text-center text-slate-500">
                      No assignments found
                    </td>
                  </tr>
                ) : (
                  assignments.map((assignment) => (
                    <tr key={assignment.id} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="p-4">
                        <div>
                          <h4 className="font-medium text-slate-900">
                            {assignment.task_details?.name || assignment.task?.name || 'N/A'}
                          </h4>
                          <p className="text-xs text-slate-500 mt-1 line-clamp-1">
                            {assignment.task_details?.description || assignment.task?.description || 'No description'}
                          </p>
                        </div>
                      </td>

                      <td className="p-4">
                        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-800">
                          {assignment.department_details?.name || assignment.department?.name || 'No department'}
                        </span>
                      </td>

                      {(isAdminOrManager || isAnalyst) && (
                        <td className="p-4">
                          <div className="flex items-center">
                            <div className="flex-shrink-0 h-8 w-8 bg-indigo-100 rounded-full flex items-center justify-center">
                              <User className="w-4 h-4 text-indigo-600" />
                            </div>
                            <div className="ml-3">
                              <p className="text-sm font-medium text-slate-900">
                                {assignment.user_details?.full_name || assignment.user?.full_name || 'N/A'}
                              </p>
                              <p className="text-xs text-slate-500">
                                {assignment.user_details?.work_mail_address || assignment.user?.work_mail_address || ''}
                              </p>
                            </div>
                          </div>
                        </td>
                      )}

                      {isEmployee && (
                        <td className="p-4">
                          <div className="flex items-center">
                            <div className="flex-shrink-0 h-8 w-8 bg-purple-100 rounded-full flex items-center justify-center">
                              <User className="w-4 h-4 text-purple-600" />
                            </div>
                            <div className="ml-3">
                              <p className="text-sm font-medium text-slate-900">
                                {assignment.assigned_by_details?.full_name || 'System'}
                              </p>
                              <p className="text-xs text-slate-500 capitalize">
                                {assignment.assigned_by_details?.role || 'System'}
                              </p>
                            </div>
                          </div>
                        </td>
                      )}

                      <td className="p-4">
                        <div className="text-sm">
                          <div className="flex items-center text-slate-900">
                            <Calendar className="w-3.5 h-3.5 mr-1 text-slate-400" />
                            {formatDate(assignment.start_time)}
                          </div>
                          <div className="flex items-center text-slate-600 text-xs mt-1">
                            <Clock className="w-3.5 h-3.5 mr-1 text-slate-400" />
                            {formatTime(assignment.start_time)} - {formatTime(assignment.end_time)}
                          </div>
                        </div>
                      </td>

                      <td className="p-4">
                        <div className="text-sm">
                          <span className="font-medium">
                            {getDurationHours(assignment.start_time, assignment.end_time)} hrs
                          </span>
                          {assignment.duration_days > 0 && (
                            <span className="text-xs text-slate-500 block">
                              ({assignment.duration_days} {assignment.duration_days === 1 ? 'day' : 'days'})
                            </span>
                          )}
                        </div>
                      </td>

                      <td className="p-4">
                        <StatusUpdateCell assignment={assignment} />
                        {assignment.is_overdue && assignment.status === ASSIGNMENT_STATUSES.SCHEDULED && (
                          <span className="ml-2 text-xs bg-red-100 text-red-700 px-2 py-1 rounded-full inline-block mt-1">
                            Overdue
                          </span>
                        )}
                      </td>

                      <td className="p-4">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${getPriorityColor(assignment.priority)}`}>
                          {assignment.priority}
                        </span>
                      </td>

                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => openModal('details', { item: assignment, type: 'assignment' })}
                            className="p-2 hover:bg-slate-100 rounded-lg text-slate-600 hover:text-slate-900"
                            title="View Details"
                          >
                            <Eye className="w-4 h-4" />
                          </button>

                          {isEmployee && assignment.user_details?.id === user?.id && (
                            <>
                              {assignment.status === ASSIGNMENT_STATUSES.SCHEDULED && assignment.can_start && (
                                <button
                                  onClick={() => startAssignment(assignment.id)}
                                  className="px-3 py-1 bg-sky-600 text-white text-sm rounded-lg hover:bg-sky-700 flex items-center"
                                >
                                  <Play className="w-3 h-3 mr-1" />
                                  Start
                                </button>
                              )}
                              {assignment.status === ASSIGNMENT_STATUSES.ACTIVE && (
                                <button
                                  onClick={() => completeAssignment(assignment.id)}
                                  className="px-3 py-1 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 flex items-center"
                                >
                                  <CheckCircle2 className="w-3 h-3 mr-1" />
                                  Complete
                                </button>
                              )}
                            </>
                          )}

                          {permissions.canEditAssignments && (isAdminOrManager || isAnalyst) && (
                            <button
                              onClick={() => openModal('assignment', assignment)}
                              className="p-2 hover:bg-sky-50 rounded-lg text-sky-600 hover:text-sky-700"
                              title="Edit"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                          )}

                          {permissions.canDeleteAssignments && isAdminOrManager && (
                            <button
                              onClick={() => deleteAssignment(assignment.id)}
                              className="p-2 hover:bg-red-50 rounded-lg text-red-600 hover:text-red-700"
                              title="Delete"
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
        </div>
      )}

      {/* ==================== PAGINATION ==================== */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between bg-white p-4 rounded-lg border border-slate-200 shadow-sm">
          <div className="text-sm text-slate-600">
            Showing {(currentPage - 1) * itemsPerPage + 1} to {Math.min(currentPage * itemsPerPage, totalItems)} of {totalItems} results
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage === 1}
              className="p-2 border border-slate-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-50"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum;
              if (totalPages <= 5) {
                pageNum = i + 1;
              } else if (currentPage <= 3) {
                pageNum = i + 1;
              } else if (currentPage >= totalPages - 2) {
                pageNum = totalPages - 4 + i;
              } else {
                pageNum = currentPage - 2 + i;
              }

              return (
                <button
                  key={pageNum}
                  onClick={() => handlePageChange(pageNum)}
                  className={`w-10 h-10 rounded-lg ${currentPage === pageNum
                    ? 'bg-indigo-600 text-white'
                    : 'border border-slate-300 hover:bg-slate-50'
                    }`}
                >
                  {pageNum}
                </button>
              );
            })}

            <button
              onClick={() => handlePageChange(currentPage + 1)}
              disabled={currentPage === totalPages}
              className="p-2 border border-slate-300 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-50"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* ==================== CREATE/EDIT TASK MODAL ==================== */}
      {modals.task && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="mb-6">
                <h2 className="text-2xl font-semibold text-slate-900">
                  {editingTask ? 'Edit Task' : 'Create New Task'}
                </h2>
                <p className="text-slate-600 mt-1">
                  {editingTask ? 'Update the task details below' : 'Fill in the task details below'}
                </p>
              </div>

              <form onSubmit={handleTaskSubmit} className="space-y-4">
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-slate-700">
                    Task Name *
                  </label>
                  <input
                    type="text"
                    value={taskForm.name}
                    onChange={(e) => setTaskForm({ ...taskForm, name: e.target.value })}
                    placeholder="e.g., Website Redesign Project"
                    required
                    className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-slate-700">
                    Description *
                  </label>
                  <textarea
                    value={taskForm.description}
                    onChange={(e) => setTaskForm({ ...taskForm, description: e.target.value })}
                    placeholder="Detailed description of the task..."
                    rows={4}
                    required
                    className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-slate-700">
                    Status
                  </label>
                  <select
                    value={taskForm.status}
                    onChange={(e) => setTaskForm({ ...taskForm, status: e.target.value })}
                    className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  >
                    <option value={TASK_STATUSES.PENDING}>Pending</option>
                    <option value={TASK_STATUSES.ACTIVE}>Active</option>
                    <option value={TASK_STATUSES.NOT_ACTIVE}>Not Active</option>
                  </select>
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => closeModal('task')}
                    className="flex-1 px-4 py-3 border border-slate-300 rounded-lg hover:bg-slate-50"
                    disabled={loading.action}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading.action}
                    className="flex-1 px-4 py-3 bg-gradient-to-r from-sky-600 to-indigo-600 text-white rounded-lg hover:from-sky-700 hover:to-indigo-700 disabled:opacity-50 flex items-center justify-center"
                  >
                    {loading.action ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : editingTask ? (
                      'Update Task'
                    ) : (
                      'Create Task'
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* ==================== CREATE/EDIT ASSIGNMENT MODAL ==================== */}
      {modals.assignment && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-lg w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="mb-6">
                <h2 className="text-2xl font-semibold text-slate-900">
                  {editingAssignment ? 'Edit Assignment' : 'Assign Task'}
                </h2>
                <p className="text-slate-600 mt-1">
                  {editingAssignment ? 'Update the assignment details below' : 'Fill in the assignment details below'}
                </p>
              </div>

              {editingAssignment && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                  <h3 className="text-sm font-medium text-blue-700 mb-3 flex items-center">
                    <Edit2 className="w-4 h-4 mr-2" />
                    Current Assignment
                  </h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-blue-600">Task:</span>
                      <span className="font-medium text-blue-900">
                        {editingAssignment.task_details?.name || editingAssignment.task?.name}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-blue-600">Employee:</span>
                      <span className="font-medium text-blue-900">
                        {editingAssignment.user_details?.full_name || editingAssignment.user?.full_name}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-blue-600">Status:</span>
                      <span className={`px-2 py-0.5 rounded-full text-xs ${getStatusBadge(editingAssignment.status)}`}>
                        {editingAssignment.status}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              <form onSubmit={handleAssignmentSubmit} className="space-y-4">
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-slate-700">
                    Select Task *
                  </label>
                  {editingAssignment ? (
                    <input
                      type="text"
                      value={editingAssignment.task_details?.name || editingAssignment.task?.name || ''}
                      disabled
                      className="w-full p-3 border border-slate-300 rounded-lg bg-slate-50 text-slate-500"
                    />
                  ) : (
                    <select
                      value={assignmentForm.task_id}
                      onChange={(e) => setAssignmentForm({ ...assignmentForm, task_id: e.target.value })}
                      className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                      required
                    >
                      <option value="">Choose a task...</option>
                      {tasks
                        .filter(t => t.status !== TASK_STATUSES.NOT_ACTIVE)
                        .map(task => (
                          <option key={task.id} value={task.id}>
                            {task.name}
                          </option>
                        ))}
                    </select>
                  )}
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-slate-700">
                    Department *
                  </label>
                  <select
                    value={assignmentForm.department_id}
                    onChange={(e) => {
                      const deptId = e.target.value;
                      setAssignmentForm({ ...assignmentForm, department_id: deptId });
                      if (deptId) fetchEmployeesByDepartment(deptId);
                    }}
                    className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    required
                  >
                    <option value="">Choose a department...</option>
                    {departments.map(dept => (
                      <option key={dept.id} value={dept.id}>
                        {dept.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-slate-700">
                    Assign to Employee *
                  </label>
                  <div className="relative">
                    <select
                      value={assignmentForm.user_id}
                      onChange={(e) => setAssignmentForm({ ...assignmentForm, user_id: e.target.value })}
                      className={`w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent ${!assignmentForm.department_id ? 'bg-slate-50' : ''
                        }`}
                      required
                      disabled={!assignmentForm.department_id || loading.employees}
                    >
                      <option value="">
                        {!assignmentForm.department_id
                          ? 'Please select a department first'
                          : loading.employees
                            ? 'Loading employees...'
                            : 'Choose an employee...'
                        }
                      </option>
                      {filteredEmployees.map(emp => (
                        <option key={emp.id} value={emp.id}>
                          {emp.full_name} {emp.work_mail_address && `- ${emp.work_mail_address}`}
                        </option>
                      ))}
                    </select>
                    {loading.employees && (
                      <div className="absolute right-3 top-3">
                        <Loader2 className="w-5 h-5 animate-spin text-indigo-600" />
                      </div>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-slate-700">
                      Assignment Date *
                    </label>
                    <input
                      type="date"
                      value={assignmentForm.assignment_date}
                      onChange={(e) => setAssignmentForm({ ...assignmentForm, assignment_date: e.target.value })}
                      required
                      className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-slate-700">
                      Priority
                    </label>
                    <select
                      value={assignmentForm.priority}
                      onChange={(e) => setAssignmentForm({ ...assignmentForm, priority: e.target.value })}
                      className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    >
                      <option value={PRIORITIES.LOW}>Low</option>
                      <option value={PRIORITIES.MEDIUM}>Medium</option>
                      <option value={PRIORITIES.HIGH}>High</option>
                      <option value={PRIORITIES.URGENT}>Urgent</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-slate-700">
                      Start Time *
                    </label>
                    <input
                      type="datetime-local"
                      value={assignmentForm.start_time}
                      onChange={(e) => setAssignmentForm({ ...assignmentForm, start_time: e.target.value })}
                      required
                      className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-slate-700">
                      End Time *
                    </label>
                    <input
                      type="datetime-local"
                      value={assignmentForm.end_time}
                      onChange={(e) => setAssignmentForm({ ...assignmentForm, end_time: e.target.value })}
                      required
                      className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-slate-700">
                    Notes (Optional)
                  </label>
                  <textarea
                    value={assignmentForm.notes}
                    onChange={(e) => setAssignmentForm({ ...assignmentForm, notes: e.target.value })}
                    placeholder="Additional instructions or notes..."
                    rows={3}
                    className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>

                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => closeModal('assignment')}
                    className="flex-1 px-4 py-3 border border-slate-300 rounded-lg hover:bg-slate-50"
                    disabled={loading.action}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading.action || !assignmentForm.department_id || !assignmentForm.user_id}
                    className="flex-1 px-4 py-3 bg-gradient-to-r from-sky-600 to-indigo-600 text-white rounded-lg hover:from-sky-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                  >
                    {loading.action ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : editingAssignment ? (
                      <>
                        <Edit2 className="w-4 h-4 mr-2" />
                        Update Assignment
                      </>
                    ) : (
                      <>
                        <UserPlus className="w-4 h-4 mr-2" />
                        Assign Task
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* ==================== BULK ASSIGNMENT MODAL ==================== */}
      {modals.bulkAssignment && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="mb-6">
                <h2 className="text-2xl font-semibold text-slate-900">Bulk Assign Task</h2>
                <p className="text-slate-600 mt-1">Choose assignment type and target users</p>
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-slate-700 mb-3">
                  Assignment Type *
                </label>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  <button
                    type="button"
                    onClick={() => {
                      setBulkForm(prev => ({ ...prev, assignmentType: ASSIGNMENT_TYPES.SINGLE }));
                      setSelectedEmployees([]);
                      setFilteredEmployees([]);
                    }}
                    className={`p-3 rounded-lg border-2 flex flex-col items-center gap-2 transition-all ${bulkForm.assignmentType === ASSIGNMENT_TYPES.SINGLE
                      ? 'border-indigo-600 bg-indigo-50'
                      : 'border-slate-200 hover:border-indigo-300'
                      }`}
                  >
                    <User className={`w-6 h-6 ${bulkForm.assignmentType === ASSIGNMENT_TYPES.SINGLE
                      ? 'text-indigo-600'
                      : 'text-slate-500'
                      }`} />
                    <span className={`text-xs font-medium ${bulkForm.assignmentType === ASSIGNMENT_TYPES.SINGLE
                      ? 'text-indigo-600'
                      : 'text-slate-600'
                      }`}>Single User</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setBulkForm(prev => ({ ...prev, assignmentType: ASSIGNMENT_TYPES.MULTIPLE }));
                      setSelectedEmployees([]);
                      setFilteredEmployees([]);
                    }}
                    className={`p-3 rounded-lg border-2 flex flex-col items-center gap-2 transition-all ${bulkForm.assignmentType === ASSIGNMENT_TYPES.MULTIPLE
                      ? 'border-indigo-600 bg-indigo-50'
                      : 'border-slate-200 hover:border-indigo-300'
                      }`}
                  >
                    <Users className={`w-6 h-6 ${bulkForm.assignmentType === ASSIGNMENT_TYPES.MULTIPLE
                      ? 'text-indigo-600'
                      : 'text-slate-500'
                      }`} />
                    <span className={`text-xs font-medium ${bulkForm.assignmentType === ASSIGNMENT_TYPES.MULTIPLE
                      ? 'text-indigo-600'
                      : 'text-slate-600'
                      }`}>Multiple Users</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setBulkForm(prev => ({ ...prev, assignmentType: ASSIGNMENT_TYPES.DEPARTMENT }));
                      setSelectedEmployees([]);
                      setFilteredEmployees([]);
                    }}
                    className={`p-3 rounded-lg border-2 flex flex-col items-center gap-2 transition-all ${bulkForm.assignmentType === ASSIGNMENT_TYPES.DEPARTMENT
                      ? 'border-indigo-600 bg-indigo-50'
                      : 'border-slate-200 hover:border-indigo-300'
                      }`}
                  >
                    <Building2 className={`w-6 h-6 ${bulkForm.assignmentType === ASSIGNMENT_TYPES.DEPARTMENT
                      ? 'text-indigo-600'
                      : 'text-slate-500'
                      }`} />
                    <span className={`text-xs font-medium ${bulkForm.assignmentType === ASSIGNMENT_TYPES.DEPARTMENT
                      ? 'text-indigo-600'
                      : 'text-slate-600'
                      }`}>Department</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setBulkForm(prev => ({ ...prev, assignmentType: ASSIGNMENT_TYPES.ROLE_BASED }));
                      setSelectedEmployees([]);
                      setFilteredEmployees([]);
                    }}
                    className={`p-3 rounded-lg border-2 flex flex-col items-center gap-2 transition-all ${bulkForm.assignmentType === ASSIGNMENT_TYPES.ROLE_BASED
                      ? 'border-indigo-600 bg-indigo-50'
                      : 'border-slate-200 hover:border-indigo-300'
                      }`}
                  >
                    <UserCog className={`w-6 h-6 ${bulkForm.assignmentType === ASSIGNMENT_TYPES.ROLE_BASED
                      ? 'text-indigo-600'
                      : 'text-slate-500'
                      }`} />
                    <span className={`text-xs font-medium ${bulkForm.assignmentType === ASSIGNMENT_TYPES.ROLE_BASED
                      ? 'text-indigo-600'
                      : 'text-slate-600'
                      }`}>Role Based</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setBulkForm(prev => ({ ...prev, assignmentType: ASSIGNMENT_TYPES.ALL_EMPLOYEES }));
                      setSelectedEmployees([]);
                      setFilteredEmployees([]);
                    }}
                    className={`p-3 rounded-lg border-2 flex flex-col items-center gap-2 transition-all ${bulkForm.assignmentType === ASSIGNMENT_TYPES.ALL_EMPLOYEES
                      ? 'border-indigo-600 bg-indigo-50'
                      : 'border-slate-200 hover:border-indigo-300'
                      }`}
                  >
                    <Briefcase className={`w-6 h-6 ${bulkForm.assignmentType === ASSIGNMENT_TYPES.ALL_EMPLOYEES
                      ? 'text-indigo-600'
                      : 'text-slate-500'
                      }`} />
                    <span className={`text-xs font-medium ${bulkForm.assignmentType === ASSIGNMENT_TYPES.ALL_EMPLOYEES
                      ? 'text-indigo-600'
                      : 'text-slate-600'
                      }`}>All Employees</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setBulkForm(prev => ({ ...prev, assignmentType: ASSIGNMENT_TYPES.ALL_USERS }));
                      setSelectedEmployees([]);
                      setFilteredEmployees([]);
                    }}
                    className={`p-3 rounded-lg border-2 flex flex-col items-center gap-2 transition-all ${bulkForm.assignmentType === ASSIGNMENT_TYPES.ALL_USERS
                      ? 'border-indigo-600 bg-indigo-50'
                      : 'border-slate-200 hover:border-indigo-300'
                      }`}
                  >
                    <Users className={`w-6 h-6 ${bulkForm.assignmentType === ASSIGNMENT_TYPES.ALL_USERS
                      ? 'text-indigo-600'
                      : 'text-slate-500'
                      }`} />
                    <span className={`text-xs font-medium ${bulkForm.assignmentType === ASSIGNMENT_TYPES.ALL_USERS
                      ? 'text-indigo-600'
                      : 'text-slate-600'
                      }`}>All Users</span>
                  </button>
                </div>
              </div>

              <form onSubmit={handleBulkSubmit} className="space-y-4">
                <div className="space-y-2">
                  <label className="block text-sm font-medium text-slate-700">
                    Select Task *
                  </label>
                  <select
                    value={bulkForm.task_id}
                    onChange={(e) => setBulkForm({ ...bulkForm, task_id: e.target.value })}
                    className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    required
                  >
                    <option value="">Choose a task...</option>
                    {tasks
                      .filter(t => t.status !== TASK_STATUSES.NOT_ACTIVE)
                      .map(task => (
                        <option key={task.id} value={task.id}>
                          {task.name}
                        </option>
                      ))}
                  </select>
                </div>

                {[ASSIGNMENT_TYPES.SINGLE, ASSIGNMENT_TYPES.MULTIPLE, ASSIGNMENT_TYPES.DEPARTMENT].includes(
                  bulkForm.assignmentType
                ) && (
                    <div className="space-y-2">
                      <label className="block text-sm font-medium text-slate-700">
                        Select Department {bulkForm.assignmentType === ASSIGNMENT_TYPES.DEPARTMENT ? '*' : ''}
                      </label>
                      <select
                        value={bulkForm.department_id}
                        onChange={handleBulkDepartmentChange}
                        className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                        required={bulkForm.assignmentType === ASSIGNMENT_TYPES.DEPARTMENT}
                      >
                        <option value="">Choose a department...</option>
                        {departments.map(dept => (
                          <option key={dept.id} value={dept.id}>
                            {dept.name}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                {bulkForm.assignmentType === ASSIGNMENT_TYPES.ROLE_BASED && (
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-slate-700">
                      Select Role *
                    </label>
                    <select
                      value={bulkForm.role}
                      onChange={(e) => setBulkForm({ ...bulkForm, role: e.target.value })}
                      className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                      required
                    >
                      <option value="">Choose a role...</option>
                      <option value={USER_ROLES.EMPLOYEE}>Employees</option>
                      <option value={USER_ROLES.MANAGER}>Managers</option>
                      <option value={USER_ROLES.ANALYST}>Analysts</option>
                      <option value={USER_ROLES.ADMIN}>Admins</option>
                    </select>
                  </div>
                )}

                {[ASSIGNMENT_TYPES.SINGLE, ASSIGNMENT_TYPES.MULTIPLE].includes(
                  bulkForm.assignmentType
                ) && bulkForm.department_id && (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <label className="block text-sm font-medium text-slate-700">
                          {bulkForm.assignmentType === ASSIGNMENT_TYPES.SINGLE
                            ? 'Select Employee *'
                            : 'Select Employees *'}
                        </label>

                        {bulkForm.assignmentType === ASSIGNMENT_TYPES.MULTIPLE && (
                          <div className="flex items-center gap-2">
                            <button
                              type="button"
                              onClick={handleSelectAllEmployees}
                              className="text-xs text-indigo-600 hover:text-indigo-700 font-medium"
                            >
                              Select All
                            </button>
                            <span className="text-xs text-slate-300">|</span>
                            <button
                              type="button"
                              onClick={handleClearSelection}
                              className="text-xs text-slate-600 hover:text-slate-700 font-medium"
                            >
                              Clear
                            </button>
                          </div>
                        )}
                      </div>

                      {loading.employees ? (
                        <div className="flex items-center justify-center py-8">
                          <Loader2 className="w-8 h-8 animate-spin text-indigo-600" />
                        </div>
                      ) : (
                        <>
                          {bulkForm.assignmentType === ASSIGNMENT_TYPES.SINGLE ? (
                            <select
                              value={selectedEmployees[0] || ''}
                              onChange={(e) => {
                                const userId = e.target.value;
                                setSelectedEmployees(userId ? [userId] : []);
                                setBulkForm(prev => ({
                                  ...prev,
                                  user_ids: userId ? [userId] : []
                                }));
                              }}
                              className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                              required
                            >
                              <option value="">Choose an employee...</option>
                              {filteredEmployees.map(emp => (
                                <option key={emp.id} value={emp.id}>
                                  {emp.full_name} {emp.work_mail_address && `- ${emp.work_mail_address}`}
                                </option>
                              ))}
                            </select>
                          ) : (
                            <div className="border border-slate-200 rounded-lg max-h-60 overflow-y-auto">
                              {filteredEmployees.length === 0 ? (
                                <p className="text-center text-slate-500 py-4">
                                  No employees found in this department
                                </p>
                              ) : (
                                filteredEmployees.map(emp => (
                                  <label
                                    key={emp.id}
                                    className="flex items-center p-3 hover:bg-slate-50 border-b border-slate-100 last:border-b-0 cursor-pointer"
                                  >
                                    <input
                                      type="checkbox"
                                      checked={selectedEmployees.includes(emp.id)}
                                      onChange={() => handleEmployeeSelection(emp.id)}
                                      className="w-4 h-4 text-indigo-600 rounded border-slate-300 focus:ring-indigo-500"
                                    />
                                    <div className="ml-3 flex-1">
                                      <p className="text-sm font-medium text-slate-900">{emp.full_name}</p>
                                      <p className="text-xs text-slate-500">{emp.work_mail_address}</p>
                                    </div>
                                  </label>
                                ))
                              )}
                            </div>
                          )}
                        </>
                      )}

                      {bulkForm.assignmentType === ASSIGNMENT_TYPES.MULTIPLE && (
                        <p className="text-xs text-slate-500">
                          {selectedEmployees.length} employee{selectedEmployees.length !== 1 ? 's' : ''} selected
                        </p>
                      )}
                    </div>
                  )}

                {[ASSIGNMENT_TYPES.DEPARTMENT, ASSIGNMENT_TYPES.ROLE_BASED].includes(
                  bulkForm.assignmentType
                ) && bulkForm.department_id && (
                    <div className="space-y-2">
                      <label className="block text-sm font-medium text-slate-700">
                        Exclude Users (Optional)
                      </label>
                      <p className="text-xs text-slate-500 mb-2">
                        Select users to exclude from this assignment
                      </p>

                      {loading.employees ? (
                        <div className="flex items-center justify-center py-4">
                          <Loader2 className="w-6 h-6 animate-spin text-indigo-600" />
                        </div>
                      ) : (
                        <div className="border border-slate-200 rounded-lg max-h-40 overflow-y-auto">
                          {filteredEmployees.map(emp => (
                            <label
                              key={emp.id}
                              className="flex items-center p-2 hover:bg-slate-50 border-b border-slate-100 last:border-b-0 cursor-pointer"
                            >
                              <input
                                type="checkbox"
                                checked={bulkForm.exclude_user_ids?.includes(emp.id)}
                                onChange={(e) => {
                                  const isChecked = e.target.checked;
                                  setBulkForm(prev => ({
                                    ...prev,
                                    exclude_user_ids: isChecked
                                      ? [...(prev.exclude_user_ids || []), emp.id]
                                      : (prev.exclude_user_ids || []).filter(id => id !== emp.id)
                                  }));
                                }}
                                className="w-4 h-4 text-red-600 rounded border-slate-300 focus:ring-red-500"
                              />
                              <span className="ml-2 text-sm text-slate-700">{emp.full_name}</span>
                            </label>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-slate-700">
                      Assignment Date *
                    </label>
                    <input
                      type="date"
                      value={bulkForm.assignment_date}
                      onChange={(e) => setBulkForm({ ...bulkForm, assignment_date: e.target.value })}
                      required
                      className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-slate-700">
                      Priority
                    </label>
                    <select
                      value={bulkForm.priority}
                      onChange={(e) => setBulkForm({ ...bulkForm, priority: e.target.value })}
                      className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    >
                      <option value={PRIORITIES.LOW}>Low</option>
                      <option value={PRIORITIES.MEDIUM}>Medium</option>
                      <option value={PRIORITIES.HIGH}>High</option>
                      <option value={PRIORITIES.URGENT}>Urgent</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-slate-700">
                      Start Time *
                    </label>
                    <input
                      type="datetime-local"
                      value={bulkForm.start_time}
                      onChange={(e) => setBulkForm({ ...bulkForm, start_time: e.target.value })}
                      required
                      className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>

                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-slate-700">
                      End Time *
                    </label>
                    <input
                      type="datetime-local"
                      value={bulkForm.end_time}
                      onChange={(e) => setBulkForm({ ...bulkForm, end_time: e.target.value })}
                      required
                      className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <label className="block text-sm font-medium text-slate-700">
                    Notes (Optional)
                  </label>
                  <textarea
                    value={bulkForm.notes}
                    onChange={(e) => setBulkForm({ ...bulkForm, notes: e.target.value })}
                    placeholder="Additional instructions or notes for all assignees..."
                    rows={3}
                    className="w-full p-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>

                {bulkAssignmentResult && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-green-700 mb-3 flex items-center">
                      <CheckCircle2 className="w-4 h-4 mr-2" />
                      Assignment Complete
                    </h4>
                    <div className="grid grid-cols-3 gap-2 text-center">
                      <div className="bg-white bg-opacity-50 p-2 rounded">
                        <p className="text-lg font-bold text-green-600">{bulkAssignmentResult.created_count}</p>
                        <p className="text-xs text-green-700">Created</p>
                      </div>
                      <div className="bg-white bg-opacity-50 p-2 rounded">
                        <p className="text-lg font-bold text-yellow-600">{bulkAssignmentResult.skipped_count}</p>
                        <p className="text-xs text-yellow-700">Skipped</p>
                      </div>
                      <div className="bg-white bg-opacity-50 p-2 rounded">
                        <p className="text-lg font-bold text-red-600">{bulkAssignmentResult.failed_count}</p>
                        <p className="text-xs text-red-700">Failed</p>
                      </div>
                    </div>
                    <p className="text-xs text-green-600 mt-2">
                      Closing automatically in 3 seconds...
                    </p>
                  </div>
                )}

                <div className="flex gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => closeModal('bulkAssignment')}
                    className="flex-1 px-4 py-3 border border-slate-300 rounded-lg hover:bg-slate-50"
                    disabled={loading.action}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={
                      loading.action ||
                      !bulkForm.task_id ||
                      (bulkForm.assignmentType === ASSIGNMENT_TYPES.SINGLE && selectedEmployees.length === 0) ||
                      (bulkForm.assignmentType === ASSIGNMENT_TYPES.MULTIPLE && selectedEmployees.length === 0) ||
                      (bulkForm.assignmentType === ASSIGNMENT_TYPES.DEPARTMENT && !bulkForm.department_id) ||
                      (bulkForm.assignmentType === ASSIGNMENT_TYPES.ROLE_BASED && !bulkForm.role)
                    }
                    className="flex-1 px-4 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white rounded-lg hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                  >
                    {loading.action ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <>
                        <Users className="w-4 h-4 mr-2" />
                        {bulkForm.assignmentType === ASSIGNMENT_TYPES.SINGLE && 'Assign Task'}
                        {bulkForm.assignmentType === ASSIGNMENT_TYPES.MULTIPLE && `Assign to ${selectedEmployees.length} Users`}
                        {bulkForm.assignmentType === ASSIGNMENT_TYPES.DEPARTMENT && 'Assign to Department'}
                        {bulkForm.assignmentType === ASSIGNMENT_TYPES.ROLE_BASED && `Assign to ${bulkForm.role || 'Role'}`}
                        {bulkForm.assignmentType === ASSIGNMENT_TYPES.ALL_EMPLOYEES && 'Assign to All Employees'}
                        {bulkForm.assignmentType === ASSIGNMENT_TYPES.ALL_USERS && 'Assign to All Users'}
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* ==================== DETAILS MODAL ==================== */}
      {modals.details && selectedItem && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-semibold text-slate-900">
                    {selectedItemType === 'task'
                      ? selectedItem.name
                      : selectedItem.task_details?.name || selectedItem.task?.name}
                  </h2>
                  <p className="text-slate-600 mt-1">
                    {selectedItemType === 'task' ? 'Task Details' : 'Assignment Details'}
                  </p>
                </div>
                <button
                  onClick={() => closeModal('details')}
                  className="p-2 hover:bg-slate-100 rounded-lg"
                >
                  <X className="w-5 h-5 text-slate-500" />
                </button>
              </div>

              {selectedItemType === 'task' ? (
                <div className="space-y-6">
                  <div>
                    <h3 className="text-sm font-medium text-slate-700 mb-2">Description</h3>
                    <p className="text-slate-900 bg-slate-50 p-4 rounded-lg">
                      {selectedItem.description}
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h3 className="text-sm font-medium text-slate-700 mb-2">Status</h3>
                      <div className="flex items-center">
                        {getStatusIcon(selectedItem.status)}
                        <span className="ml-2 capitalize">{selectedItem.status}</span>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-sm font-medium text-slate-700 mb-2">Created</h3>
                      <p className="text-slate-900">{formatDateTime(selectedItem.created_at)}</p>
                    </div>

                    <div>
                      <h3 className="text-sm font-medium text-slate-700 mb-2">Last Updated</h3>
                      <p className="text-slate-900">{formatDateTime(selectedItem.updated_at)}</p>
                    </div>

                    <div>
                      <h3 className="text-sm font-medium text-slate-700 mb-2">Created By</h3>
                      <div className="flex items-center">
                        <User className="w-4 h-4 text-slate-400 mr-2" />
                        <span className="text-slate-900">
                          {selectedItem.created_by?.full_name || 'System'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-6">
                  <div className="border-b border-slate-200 pb-4">
                    <h3 className="text-sm font-medium text-slate-700 mb-3 flex items-center">
                      <CheckCircle2 className="w-4 h-4 mr-2 text-indigo-600" />
                      Task Information
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs text-slate-500">Task Name</p>
                        <p className="text-sm font-medium text-slate-900">
                          {selectedItem.task_details?.name || selectedItem.task?.name || 'N/A'}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500">Task Status</p>
                        <div className="flex items-center mt-1">
                          {getStatusIcon(selectedItem.task_details?.status || selectedItem.task?.status)}
                          <span className="ml-2 text-sm capitalize">
                            {selectedItem.task_details?.status || selectedItem.task?.status || 'N/A'}
                          </span>
                        </div>
                      </div>
                      {(selectedItem.task_details?.description || selectedItem.task?.description) && (
                        <div className="col-span-2">
                          <p className="text-xs text-slate-500">Task Description</p>
                          <p className="text-sm text-slate-900 bg-slate-50 p-3 rounded-lg mt-1">
                            {selectedItem.task_details?.description || selectedItem.task?.description}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="border-b border-slate-200 pb-4">
                    <h3 className="text-sm font-medium text-slate-700 mb-3 flex items-center">
                      <User className="w-4 h-4 mr-2 text-indigo-600" />
                      Assignment Details
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs text-slate-500">Assigned To</p>
                        <div className="flex items-center mt-1">
                          <div className="flex-shrink-0 h-8 w-8 bg-indigo-100 rounded-full flex items-center justify-center">
                            <User className="w-4 h-4 text-indigo-600" />
                          </div>
                          <div className="ml-2">
                            <p className="text-sm font-medium text-slate-900">
                              {selectedItem.user_details?.full_name || selectedItem.user?.full_name || 'N/A'}
                            </p>
                            <p className="text-xs text-slate-500">
                              {selectedItem.user_details?.work_mail_address || selectedItem.user?.work_mail_address || ''}
                            </p>
                          </div>
                        </div>
                      </div>

                      <div>
                        <p className="text-xs text-slate-500">Assigned By</p>
                        <div className="flex items-center mt-1">
                          <div className="flex-shrink-0 h-8 w-8 bg-purple-100 rounded-full flex items-center justify-center">
                            <User className="w-4 h-4 text-purple-600" />
                          </div>
                          <div className="ml-2">
                            <p className="text-sm font-medium text-slate-900">
                              {selectedItem.assigned_by_details?.full_name || 'System'}
                            </p>
                            <p className="text-xs text-slate-500 capitalize">
                              {selectedItem.assigned_by_details?.role || 'System'}
                            </p>
                          </div>
                        </div>
                      </div>

                      <div>
                        <p className="text-xs text-slate-500">Department</p>
                        <span className="inline-flex items-center px-2.5 py-1 mt-1 rounded-full text-xs font-medium bg-slate-100 text-slate-800">
                          {selectedItem.department_details?.name || selectedItem.department?.name || 'No department'}
                        </span>
                      </div>

                      <div>
                        <p className="text-xs text-slate-500">Assignment Date</p>
                        <p className="text-sm font-medium text-slate-900 mt-1">
                          {formatDate(selectedItem.assignment_date)}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="border-b border-slate-200 pb-4">
                    <h3 className="text-sm font-medium text-slate-700 mb-3 flex items-center">
                      <Clock className="w-4 h-4 mr-2 text-indigo-600" />
                      Schedule Information
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs text-slate-500">Scheduled Start</p>
                        <p className="text-sm font-medium text-slate-900 mt-1">
                          {formatDateTime(selectedItem.start_time)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500">Scheduled End</p>
                        <p className="text-sm font-medium text-slate-900 mt-1">
                          {formatDateTime(selectedItem.end_time)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-slate-500">Duration</p>
                        <p className="text-sm font-medium text-slate-900 mt-1">
                          {getDurationHours(selectedItem.start_time, selectedItem.end_time)} hours
                        </p>
                        {selectedItem.duration_days > 0 && (
                          <p className="text-xs text-slate-500">
                            ({selectedItem.duration_days} {selectedItem.duration_days === 1 ? 'day' : 'days'})
                          </p>
                        )}
                      </div>
                      <div>
                        <p className="text-xs text-slate-500">Priority</p>
                        <span className={`inline-flex items-center px-2.5 py-1 mt-1 rounded-full text-xs font-medium ${getPriorityColor(selectedItem.priority)}`}>
                          {selectedItem.priority}
                        </span>
                      </div>
                    </div>
                  </div>

                  {(selectedItem.actual_start_time || selectedItem.actual_end_time) && (
                    <div className="border-b border-slate-200 pb-4">
                      <h3 className="text-sm font-medium text-slate-700 mb-3 flex items-center">
                        <CheckCircle2 className="w-4 h-4 mr-2 text-green-600" />
                        Actual Timing
                      </h3>
                      <div className="grid grid-cols-2 gap-4">
                        {selectedItem.actual_start_time && (
                          <div>
                            <p className="text-xs text-slate-500">Actual Start</p>
                            <p className="text-sm font-medium text-slate-900 mt-1">
                              {formatDateTime(selectedItem.actual_start_time)}
                            </p>
                          </div>
                        )}
                        {selectedItem.actual_end_time && (
                          <div>
                            <p className="text-xs text-slate-500">Actual End</p>
                            <p className="text-sm font-medium text-slate-900 mt-1">
                              {formatDateTime(selectedItem.actual_end_time)}
                            </p>
                          </div>
                        )}
                        {selectedItem.actual_start_time && selectedItem.actual_end_time && (
                          <div>
                            <p className="text-xs text-slate-500">Actual Duration</p>
                            <p className="text-sm font-medium text-slate-900 mt-1">
                              {selectedItem.actual_duration_minutes
                                ? `${(selectedItem.actual_duration_minutes / 60).toFixed(1)} hours`
                                : 'N/A'}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  <div className="border-b border-slate-200 pb-4">
                    <h3 className="text-sm font-medium text-slate-700 mb-3 flex items-center">
                      <AlertCircle className="w-4 h-4 mr-2 text-indigo-600" />
                      Status Information
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs text-slate-500">Current Status</p>
                        <div className="flex items-center mt-1">
                          {getStatusIcon(selectedItem.status)}
                          <span className="ml-2 text-sm capitalize font-medium">{selectedItem.status}</span>
                          {selectedItem.is_overdue && selectedItem.status === ASSIGNMENT_STATUSES.SCHEDULED && (
                            <span className="ml-2 text-xs bg-red-100 text-red-700 px-2 py-1 rounded-full">
                              Overdue
                            </span>
                          )}
                        </div>
                      </div>
                      {selectedItem.is_current && (
                        <div>
                          <p className="text-xs text-slate-500">Currently Active</p>
                          <span className="inline-flex items-center mt-1 px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-700">
                            In Progress
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  {selectedItem.is_modified && (
                    <div className="border-b border-slate-200 pb-4">
                      <h3 className="text-sm font-medium text-slate-700 mb-3 flex items-center">
                        <Edit2 className="w-4 h-4 mr-2 text-orange-600" />
                        Modification History
                      </h3>
                      <div className="bg-orange-50 p-3 rounded-lg">
                        <p className="text-xs text-orange-700 mb-1">
                          Modified by: {selectedItem.modified_by_details?.full_name || 'Unknown'}
                        </p>
                        <p className="text-xs text-orange-600">
                          Reason: {selectedItem.modification_reason || 'No reason provided'}
                        </p>
                        <p className="text-xs text-slate-500 mt-1">
                          {formatDateTime(selectedItem.updated_at)}
                        </p>
                      </div>
                    </div>
                  )}

                  {selectedItem.notes && (
                    <div>
                      <h3 className="text-sm font-medium text-slate-700 mb-2 flex items-center">
                        <Edit2 className="w-4 h-4 mr-2 text-slate-600" />
                        Additional Notes
                      </h3>
                      <p className="text-sm text-slate-900 bg-slate-50 p-4 rounded-lg">
                        {selectedItem.notes}
                      </p>
                    </div>
                  )}
                </div>
              )}

              <div className="flex gap-3 pt-6 mt-6 border-t border-slate-200">
                <button
                  onClick={() => closeModal('details')}
                  className="flex-1 px-4 py-3 border border-slate-300 rounded-lg hover:bg-slate-50"
                >
                  Close
                </button>

                {selectedItemType === 'task' && permissions.canEditTasks && (
                  <button
                    onClick={() => {
                      closeModal('details');
                      openModal('task', selectedItem);
                    }}
                    className="flex-1 px-4 py-3 bg-gradient-to-r from-sky-600 to-indigo-600 text-white rounded-lg hover:from-sky-700 hover:to-indigo-700"
                  >
                    Edit Task
                  </button>
                )}

                {selectedItemType === 'assignment' && permissions.canEditAssignments && (
                  <button
                    onClick={() => {
                      closeModal('details');
                      openModal('assignment', selectedItem);
                    }}
                    className="flex-1 px-4 py-3 bg-gradient-to-r from-sky-600 to-indigo-600 text-white rounded-lg hover:from-sky-700 hover:to-indigo-700"
                  >
                    Edit Assignment
                  </button>
                )}

                {selectedItemType === 'assignment' &&
                  isEmployee &&
                  selectedItem.user_details?.id === user?.id &&
                  selectedItem.status === ASSIGNMENT_STATUSES.SCHEDULED &&
                  selectedItem.can_start && (
                    <button
                      onClick={() => {
                        closeModal('details');
                        startAssignment(selectedItem.id);
                      }}
                      className="flex-1 px-4 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg hover:from-green-700 hover:to-emerald-700"
                    >
                      Start Task
                    </button>
                  )}

                {selectedItemType === 'assignment' &&
                  isEmployee &&
                  selectedItem.user_details?.id === user?.id &&
                  selectedItem.status === ASSIGNMENT_STATUSES.ACTIVE && (
                    <button
                      onClick={() => {
                        closeModal('details');
                        completeAssignment(selectedItem.id);
                      }}
                      className="flex-1 px-4 py-3 bg-gradient-to-r from-green-600 to-emerald-600 text-white rounded-lg hover:from-green-700 hover:to-emerald-700"
                    >
                      Complete Task
                    </button>
                  )}
              </div>
            </div>
          </div>
        </div>
      )}


      {/* ==================== STATUS UPDATE RESPONSE MODAL ==================== */}
      {statusUpdateResponse.show && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[100] p-4">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto animate-in fade-in zoom-in duration-300">
            <div className="p-6">
              {/* Modal Header */}
              <div className="flex items-start justify-between mb-6">
                <div>
                  <h2 className="text-2xl font-semibold text-slate-900 flex items-center">
                    {statusUpdateResponse.loading ? (
                      <>
                        <Loader2 className="w-6 h-6 animate-spin text-indigo-600 mr-2" />
                        Updating Status...
                      </>
                    ) : statusUpdateResponse.error ? (
                      <>
                        <AlertTriangle className="w-6 h-6 text-red-600 mr-2" />
                        Update Failed
                      </>
                    ) : (
                      <>
                        <CheckCircle2 className="w-6 h-6 text-green-600 mr-2" />
                        Status Updated Successfully
                      </>
                    )}
                  </h2>
                  <p className="text-slate-600 mt-1">
                    {statusUpdateResponse.loading
                      ? 'Please wait while we update the assignment status...'
                      : statusUpdateResponse.error
                        ? 'An error occurred while updating the status'
                        : 'The assignment status has been updated'
                    }
                  </p>
                </div>
                <button
                  onClick={() => setStatusUpdateResponse(prev => ({ ...prev, show: false }))}
                  className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                  disabled={statusUpdateResponse.loading}
                >
                  <X className="w-5 h-5 text-slate-500" />
                </button>
              </div>

              {/* Loading State */}
              {statusUpdateResponse.loading && (
                <div className="flex flex-col items-center justify-center py-12">
                  <Loader2 className="w-12 h-12 animate-spin text-indigo-600 mb-4" />
                  <p className="text-slate-600">Processing your request...</p>
                </div>
              )}

              {/* Error State */}
              {!statusUpdateResponse.loading && statusUpdateResponse.error && (
                <div className="space-y-4">
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex items-start">
                      <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5 mr-3 flex-shrink-0" />
                      <div>
                        <h3 className="text-sm font-medium text-red-800 mb-1">Error Details</h3>
                        <p className="text-sm text-red-700">{statusUpdateResponse.error}</p>
                      </div>
                    </div>
                  </div>

                  {/* Show raw response data if available */}
                  {statusUpdateResponse.data && (
                    <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                      <h3 className="text-sm font-medium text-slate-700 mb-2 flex items-center">
                        <AlertCircle className="w-4 h-4 mr-2 text-slate-500" />
                        Response Details
                      </h3>
                      <pre className="text-xs bg-white p-3 rounded border border-slate-200 overflow-auto max-h-60">
                        {JSON.stringify(statusUpdateResponse.data, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              )}

              {/* Success State */}
              {!statusUpdateResponse.loading && !statusUpdateResponse.error && statusUpdateResponse.data && (
                <div className="space-y-6">
                  {/* Success Message */}
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <div className="flex items-start">
                      <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5 mr-3 flex-shrink-0" />
                      <div>
                        <h3 className="text-sm font-medium text-green-800 mb-1">Success</h3>
                        <p className="text-sm text-green-700">
                          {statusUpdateResponse.data.message || 'Status updated successfully'}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Assignment Details */}
                  {statusUpdateResponse.data.assignment && (
                    <div className="border border-slate-200 rounded-lg divide-y divide-slate-200">
                      <div className="p-4 bg-slate-50 rounded-t-lg">
                        <h3 className="text-sm font-medium text-slate-700 flex items-center">
                          <Briefcase className="w-4 h-4 mr-2 text-indigo-600" />
                          Updated Assignment Details
                        </h3>
                      </div>

                      <div className="p-4 space-y-3">
                        {/* Status Change */}
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-slate-600">New Status:</span>
                          <div className="flex items-center">
                            {getStatusIcon(statusUpdateResponse.data.assignment.status)}
                            <span className="ml-2 text-sm font-medium capitalize">
                              {statusUpdateResponse.data.assignment.status}
                            </span>
                          </div>
                        </div>

                        {/* Task Info */}
                        <div className="flex items-start justify-between">
                          <span className="text-sm text-slate-600">Task:</span>
                          <span className="text-sm font-medium text-right">
                            {statusUpdateResponse.data.assignment.task_details?.name ||
                              statusUpdateResponse.data.assignment.task?.name || 'N/A'}
                          </span>
                        </div>

                        {/* User Info */}
                        <div className="flex items-start justify-between">
                          <span className="text-sm text-slate-600">Assigned To:</span>
                          <span className="text-sm font-medium">
                            {statusUpdateResponse.data.assignment.user_details?.full_name ||
                              statusUpdateResponse.data.assignment.user?.full_name || 'N/A'}
                          </span>
                        </div>

                        {/* Timestamps */}
                        <div className="flex items-start justify-between">
                          <span className="text-sm text-slate-600">Updated At:</span>
                          <span className="text-sm font-medium">
                            {formatDateTime(statusUpdateResponse.data.assignment.updated_at)}
                          </span>
                        </div>

                        {/* Show reason if provided */}
                        {statusUpdateResponse.data.assignment.modification_reason && (
                          <div className="mt-2 pt-2 border-t border-slate-100">
                            <span className="text-sm text-slate-600 block mb-1">Reason:</span>
                            <p className="text-sm bg-slate-50 p-2 rounded">
                              {statusUpdateResponse.data.assignment.modification_reason}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Raw Response (for debugging/transparency) */}
                  <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                    <details>
                      <summary className="text-sm font-medium text-slate-700 cursor-pointer flex items-center">
                        <ChevronDown className="w-4 h-4 mr-2" />
                        View Full Response
                      </summary>
                      <pre className="text-xs bg-white p-3 rounded border border-slate-200 overflow-auto max-h-60 mt-3">
                        {JSON.stringify(statusUpdateResponse.data, null, 2)}
                      </pre>
                    </details>
                  </div>

                  {/* Auto-close message */}
                  <p className="text-xs text-center text-slate-500">
                    This modal will close automatically in 5 seconds...
                  </p>
                </div>
              )}

              {/* Modal Footer */}
              <div className="flex gap-3 pt-6 mt-6 border-t border-slate-200">
                <button
                  onClick={() => setStatusUpdateResponse(prev => ({ ...prev, show: false }))}
                  className="flex-1 px-4 py-3 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
                  disabled={statusUpdateResponse.loading}
                >
                  Close
                </button>

                {!statusUpdateResponse.loading && statusUpdateResponse.error && (
                  <button
                    onClick={() => {
                      // Retry logic - you might want to store the last attempted update
                      setStatusUpdateResponse(prev => ({ ...prev, show: false }));
                    }}
                    className="flex-1 px-4 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
                  >
                    Try Again
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}