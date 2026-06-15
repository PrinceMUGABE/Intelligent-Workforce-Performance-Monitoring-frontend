import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Plus, Edit2, Trash2, Users, Search, Building, Activity, 
  RefreshCw, Filter, Calendar, ChevronDown, ChevronUp,
  Eye, X, Download, Upload, ChevronLeft, ChevronRight,
  BarChart3, UserPlus, CheckCircle, XCircle, Info,
  SortAsc, SortDesc, Mail, Phone, User, Clock, Hash
} from 'lucide-react';
import { toast } from 'sonner';
import { Toaster } from 'sonner';
import { useAuth, api } from '../../context/auth-context';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";

// API base URL
const API_BASE_URL = 'http://127.0.0.1:8000';

export default function DepartmentsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [departments, setDepartments] = useState([]);
  const [filteredDepartments, setFilteredDepartments] = useState([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false);
  const [editingDepartment, setEditingDepartment] = useState(null);
  const [selectedDepartment, setSelectedDepartment] = useState(null);
  const [departmentEmployees, setDepartmentEmployees] = useState([]);
  const [filteredEmployees, setFilteredEmployees] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [employeeSearchTerm, setEmployeeSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [employeeCurrentPage, setEmployeeCurrentPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [employeesLoading, setEmployeesLoading] = useState(false);
  
  // Advanced filters
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    status: 'all',
    dateRange: {
      startDate: null,
      endDate: null
    },
    sortBy: 'created_at',
    sortOrder: 'desc',
    minEmployees: '',
    maxEmployees: ''
  });
  
  const [stats, setStats] = useState({
    totalDepartments: 0,
    activeDepartments: 0,
    inactiveDepartments: 0,
    totalEmployees: 0,
    avgEmployeesPerDept: 0,
    departmentsCreatedThisMonth: 0,
    departmentsCreatedToday: 0
  });
  
  const itemsPerPage = 10;
  const employeesPerPage = 5;

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    status: 'active'
  });

  const [formErrors, setFormErrors] = useState({});

  // Fetch departments from API
  // Fetch departments from API
const fetchDepartments = async () => {
  setLoading(true);
  try {
    const [deptsResponse, usersResponse] = await Promise.all([
      api.get(`${API_BASE_URL}/departments/all/`),
      api.get(`${API_BASE_URL}/users/employees/`)
    ]);
    
    if (deptsResponse.data.success && usersResponse.data && usersResponse.data.users) {
      const allUsers = usersResponse.data.users;
      
      const departmentsData = deptsResponse.data.data.map(dept => {
        // Count employees in this department
        const deptUsers = allUsers.filter(user => 
          user.department === dept.id || 
          (user.department_details && user.department_details.id === dept.id)
        );
        
        return {
          ...dept,
          employeeCount: deptUsers.length
        };
      });
      
      setDepartments(departmentsData);
      applyFiltersAndSearch(departmentsData, searchTerm, filters);
      calculateStats(departmentsData);
    } else {
      toast.error('Failed to fetch departments or employees');
    }
  } catch (error) {
    console.error('Error fetching data:', error);
    toast.error('Error loading departments. Please try again.');
  } finally {
    setLoading(false);
    setRefreshing(false);
  }
};

  // Fetch employees for selected department
  const fetchDepartmentEmployees = async (departmentId) => {
    if (!departmentId) return;
    
    setEmployeesLoading(true);
    try {
      // First get all users, then filter by department
      const response = await api.get(`${API_BASE_URL}/users/employees/`);
      if (response.data && response.data.users) {
        // Filter employees by department
        const deptEmployees = response.data.users.filter(emp => 
          emp.department === departmentId || 
          (emp.department_details && emp.department_details.id === departmentId)
        );
        setDepartmentEmployees(deptEmployees);
        setFilteredEmployees(deptEmployees);
      } else {
        toast.error('Failed to fetch employees');
        setDepartmentEmployees([]);
        setFilteredEmployees([]);
      }
    } catch (error) {
      console.error('Error fetching department employees:', error);
      toast.error('Error loading employees. Please try again.');
      setDepartmentEmployees([]);
      setFilteredEmployees([]);
    } finally {
      setEmployeesLoading(false);
    }
  };

  // Calculate statistics
  const calculateStats = (depts) => {
    const totalDepartments = depts.length;
    const activeDepartments = depts.filter(dept => dept.status === 'active').length;
    const inactiveDepartments = depts.filter(dept => dept.status === 'inactive').length;
    
    // Calculate total employees across all departments
    const totalEmployees = depts.reduce((sum, dept) => {
      return sum + (dept.employeeCount || 0);
    }, 0);
    
    const avgEmployeesPerDept = totalDepartments > 0 ? 
      (totalEmployees / totalDepartments).toFixed(1) : 0;
    
    // Calculate departments created this month
    const currentMonth = new Date().getMonth();
    const currentYear = new Date().getFullYear();
    const departmentsCreatedThisMonth = depts.filter(dept => {
      const deptDate = new Date(dept.created_at);
      return deptDate.getMonth() === currentMonth && 
             deptDate.getFullYear() === currentYear;
    }).length;

    // Calculate departments created today
    const today = new Date();
    const departmentsCreatedToday = depts.filter(dept => {
      const deptDate = new Date(dept.created_at);
      return deptDate.getDate() === today.getDate() &&
             deptDate.getMonth() === today.getMonth() &&
             deptDate.getFullYear() === today.getFullYear();
    }).length;

    setStats({
      totalDepartments,
      activeDepartments,
      inactiveDepartments,
      totalEmployees,
      avgEmployeesPerDept,
      departmentsCreatedThisMonth,
      departmentsCreatedToday
    });
  };

  // Apply filters and search
  const applyFiltersAndSearch = (depts, searchTerm, filters) => {
    let filtered = [...depts];

    // Apply search term
    if (searchTerm.trim() !== '') {
      filtered = filtered.filter(dept =>
        dept.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (dept.description && dept.description.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (dept.created_by_details?.full_name?.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    // Apply status filter
    if (filters.status !== 'all') {
      filtered = filtered.filter(dept => dept.status === filters.status);
    }

    // Apply date range filter
    if (filters.dateRange.startDate && filters.dateRange.endDate) {
      filtered = filtered.filter(dept => {
        const deptDate = new Date(dept.created_at);
        const start = new Date(filters.dateRange.startDate);
        const end = new Date(filters.dateRange.endDate);
        start.setHours(0, 0, 0, 0);
        end.setHours(23, 59, 59, 999);
        return deptDate >= start && deptDate <= end;
      });
    }

    // Apply employee count filters
    if (filters.minEmployees !== '') {
      const min = parseInt(filters.minEmployees);
      filtered = filtered.filter(dept => (dept.employeeCount || 0) >= min);
    }

    if (filters.maxEmployees !== '') {
      const max = parseInt(filters.maxEmployees);
      filtered = filtered.filter(dept => (dept.employeeCount || 0) <= max);
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue, bValue;
      
      switch (filters.sortBy) {
        case 'name':
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case 'employeeCount':
          aValue = a.employeeCount || 0;
          bValue = b.employeeCount || 0;
          break;
        case 'status':
          aValue = a.status;
          bValue = b.status;
          break;
        case 'created_at':
          aValue = new Date(a.created_at);
          bValue = new Date(b.created_at);
          break;
        default:
          aValue = new Date(a.created_at);
          bValue = new Date(b.created_at);
      }

      if (filters.sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    setFilteredDepartments(filtered);
    setCurrentPage(1);
  };

  // Apply employee search
  const applyEmployeeSearch = () => {
    if (!employeeSearchTerm.trim()) {
      setFilteredEmployees(departmentEmployees);
      return;
    }

    const filtered = departmentEmployees.filter(employee =>
      employee.full_name?.toLowerCase().includes(employeeSearchTerm.toLowerCase()) ||
      employee.work_mail_address?.toLowerCase().includes(employeeSearchTerm.toLowerCase()) ||
      employee.email?.toLowerCase().includes(employeeSearchTerm.toLowerCase()) ||
      employee.phone_number?.includes(employeeSearchTerm)
    );

    setFilteredEmployees(filtered);
    setEmployeeCurrentPage(1);
  };

  // Initial fetch
  useEffect(() => {
    if (user && (user.role === 'admin' || user.role === 'manager' || user.role === 'analyst')) {
      fetchDepartments();
    }
  }, [user]);

  // Apply filters when they change
  useEffect(() => {
    applyFiltersAndSearch(departments, searchTerm, filters);
  }, [filters, searchTerm]);

  // Apply employee search when term changes
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      applyEmployeeSearch();
    }, 300);

    return () => clearTimeout(timeoutId);
  }, [employeeSearchTerm, departmentEmployees]);

  // Check if user is authorized
  if (!user || (user.role !== 'admin' && user.role !== 'manager' && user.role !== 'analyst')) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Building className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Access Denied</h2>
          <p className="text-slate-600">You don't have permission to access this page.</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  // Get role-specific description
  const getDescription = () => {
    if (user.role === 'admin') {
      return 'Manage organizational departments, their structures, and assigned managers (admin-only access)';
    }
    return 'View organizational departments and their structures';
  };

  // Department modal handlers
  const handleOpenModal = (department = null) => {
    if (department && user.role === 'admin') {
      setEditingDepartment(department);
      setFormData({
        name: department.name,
        description: department.description || '',
        status: department.status
      });
    } else if (user.role === 'admin') {
      setEditingDepartment(null);
      setFormData({
        name: '',
        description: '',
        status: 'active'
      });
    } else {
      toast.error('Only administrators can create or edit departments');
      return;
    }
    setFormErrors({});
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setEditingDepartment(null);
    setFormData({
      name: '',
      description: '',
      status: 'active'
    });
    setFormErrors({});
  };

  // Department details modal
  const handleOpenDetailsModal = async (department) => {
    setSelectedDepartment(department);
    setIsDetailsModalOpen(true);
    await fetchDepartmentEmployees(department.id);
  };

  const handleCloseDetailsModal = () => {
    setIsDetailsModalOpen(false);
    setSelectedDepartment(null);
    setDepartmentEmployees([]);
    setFilteredEmployees([]);
    setEmployeeSearchTerm('');
    setEmployeeCurrentPage(1);
  };

  // Form validation
  const validateForm = () => {
    const errors = {};
    
    if (!formData.name.trim()) {
      errors.name = 'Department name is required';
    } else if (formData.name.trim().length < 2) {
      errors.name = 'Department name must be at least 2 characters';
    }
    
    if (formData.description && formData.description.length > 500) {
      errors.description = 'Description cannot exceed 500 characters';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    
    try {
      if (editingDepartment) {
        // Update department
        const response = await api.put(`${API_BASE_URL}/departments/${editingDepartment.id}/update/`, formData);
        if (response.data.success) {
          toast.success('Department updated successfully!');
          fetchDepartments();
          handleCloseModal();
        } else {
          toast.error(response.data.message || 'Failed to update department');
        }
      } else {
        // Create new department
        const response = await api.post(`${API_BASE_URL}/departments/create/`, formData);
        if (response.data.success) {
          toast.success('Department created successfully!');
          fetchDepartments();
          handleCloseModal();
        } else {
          toast.error(response.data.message || 'Failed to create department');
        }
      }
    } catch (error) {
      console.error('Error saving department:', error);
      
      if (error.response?.data?.errors) {
        setFormErrors(error.response.data.errors);
        toast.error('Please fix the form errors');
      } else if (error.response?.data?.message) {
        toast.error(error.response.data.message);
      } else {
        toast.error('Failed to save department. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Delete department
  const handleDelete = async (departmentId, departmentName) => {
    if (!confirm(`Are you sure you want to delete department "${departmentName}"? This action cannot be undone.`)) {
      return;
    }
    
    setLoading(true);
    
    try {
      const response = await api.delete(`${API_BASE_URL}/departments/${departmentId}/delete/`);
      if (response.data.success) {
        toast.success('Department deleted successfully!');
        fetchDepartments();
      } else {
        toast.error(response.data.message || 'Failed to delete department');
      }
    } catch (error) {
      console.error('Error deleting department:', error);
      
      if (error.response?.data?.message) {
        toast.error(error.response.data.message);
      } else {
        toast.error('Failed to delete department. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchDepartments();
  };

  // Reset filters
  const handleResetFilters = () => {
    setFilters({
      status: 'all',
      dateRange: { startDate: null, endDate: null },
      sortBy: 'created_at',
      sortOrder: 'desc',
      minEmployees: '',
      maxEmployees: ''
    });
    setSearchTerm('');
  };

  // Pagination calculations
  const totalPages = Math.ceil(filteredDepartments.length / itemsPerPage);
  const paginatedDepartments = filteredDepartments.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const totalEmployeePages = Math.ceil(filteredEmployees.length / employeesPerPage);
  const paginatedEmployees = filteredEmployees.slice(
    (employeeCurrentPage - 1) * employeesPerPage,
    employeeCurrentPage * employeesPerPage
  );

  // Format date
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Status badge component
  const StatusBadge = ({ status }) => {
    const getStatusConfig = (status) => {
      switch (status) {
        case 'active':
          return {
            bg: 'bg-green-100',
            text: 'text-green-800',
            icon: <CheckCircle className="w-3 h-3 mr-1" />,
            label: 'Active'
          };
        case 'inactive':
          return {
            bg: 'bg-red-100',
            text: 'text-red-800',
            icon: <XCircle className="w-3 h-3 mr-1" />,
            label: 'Inactive'
          };
        default:
          return {
            bg: 'bg-gray-100',
            text: 'text-gray-800',
            icon: <Info className="w-3 h-3 mr-1" />,
            label: status
          };
      }
    };

    const config = getStatusConfig(status);

    return (
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.text}`}>
        {config.icon}
        {config.label}
      </span>
    );
  };

  // Employee status badge
  const EmployeeStatusBadge = ({ status }) => {
    const getStatusConfig = (status) => {
      switch (status) {
        case 'approved':
          return {
            bg: 'bg-green-100',
            text: 'text-green-800',
            label: 'Active'
          };
        case 'pending':
          return {
            bg: 'bg-yellow-100',
            text: 'text-yellow-800',
            label: 'Pending'
          };
        case 'rejected':
          return {
            bg: 'bg-red-100',
            text: 'text-red-800',
            label: 'Rejected'
          };
        default:
          return {
            bg: 'bg-gray-100',
            text: 'text-gray-800',
            label: status
          };
      }
    };

    const config = getStatusConfig(status);

    return (
      <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${config.bg} ${config.text}`}>
        {config.label}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      <Toaster position="top-right" richColors />
      
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Building className="w-8 h-8 text-indigo-600" />
            <h1 className="text-3xl font-bold text-slate-900">Department Management</h1>
          </div>
          <p className="text-slate-600">{getDescription()}</p>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
          
          {user.role === 'admin' && (
            <button
              onClick={() => handleOpenModal()}
              disabled={loading}
              className="bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
            >
              <Plus className="w-4 h-4" />
              Add Department
            </button>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-gradient-to-br from-sky-50 to-white p-6 rounded-xl border border-sky-100 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-slate-600">Total Departments</h3>
              <div className="text-3xl font-bold text-slate-900 mt-2">{stats.totalDepartments}</div>
              <div className="flex items-center gap-2 mt-2">
                <div className="flex items-center text-sm">
                  <CheckCircle className="w-4 h-4 text-green-500 mr-1" />
                  <span className="text-green-700">{stats.activeDepartments} active</span>
                </div>
                <div className="flex items-center text-sm">
                  <XCircle className="w-4 h-4 text-red-500 mr-1" />
                  <span className="text-red-700">{stats.inactiveDepartments} inactive</span>
                </div>
              </div>
            </div>
            <Building className="w-10 h-10 text-sky-500 opacity-70" />
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-green-50 to-white p-6 rounded-xl border border-green-100 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-slate-600">Total Employees</h3>
              <div className="text-3xl font-bold text-slate-900 mt-2">{stats.totalEmployees}</div>
              <div className="text-sm text-slate-500 mt-2">
                <span className="font-medium">{stats.avgEmployeesPerDept}</span> avg per department
              </div>
            </div>
            <Users className="w-10 h-10 text-green-500 opacity-70" />
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-purple-50 to-white p-6 rounded-xl border border-purple-100 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-slate-600">Created This Month</h3>
              <div className="text-3xl font-bold text-slate-900 mt-2">{stats.departmentsCreatedThisMonth}</div>
              <div className="text-sm text-slate-500 mt-2">
                <span className="font-medium">{stats.departmentsCreatedToday}</span> created today
              </div>
            </div>
            <Calendar className="w-10 h-10 text-purple-500 opacity-70" />
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-orange-50 to-white p-6 rounded-xl border border-orange-100 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-medium text-slate-600">Department Statistics</h3>
              <div className="text-3xl font-bold text-slate-900 mt-2">{stats.avgEmployeesPerDept}</div>
              <div className="text-sm text-slate-500 mt-2">
                Average employees per department
              </div>
            </div>
            <BarChart3 className="w-10 h-10 text-orange-500 opacity-70" />
          </div>
        </div>
      </div>

      {/* Search and Filters Section */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm">
        <div className="p-4 border-b border-slate-200">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="text"
                placeholder="Search departments by name, description, or creator..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
              />
              {searchTerm && (
                <button
                  onClick={() => setSearchTerm('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
            
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="px-4 py-3 border border-slate-300 rounded-lg hover:bg-slate-50 flex items-center gap-2 transition-colors"
              >
                <Filter className="w-4 h-4" />
                Filters
                {showFilters ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
              </button>
              
              {(filters.status !== 'all' || filters.dateRange.startDate || filters.minEmployees || filters.maxEmployees) && (
                <button
                  onClick={handleResetFilters}
                  className="px-4 py-3 text-sm text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded-lg border border-slate-300 transition-colors"
                >
                  Clear Filters
                </button>
              )}
            </div>
          </div>
          
          <div className="mt-2 text-sm text-slate-500">
            {filteredDepartments.length} of {departments.length} departments found
          </div>
        </div>
        
        {/* Advanced Filters */}
        {showFilters && (
          <div className="p-4 border-t border-slate-200 bg-slate-50">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Status Filter */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Status
                </label>
                <select
                  value={filters.status}
                  onChange={(e) => setFilters({...filters, status: e.target.value})}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                >
                  <option value="all">All Statuses</option>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
              
              {/* Date Range Filter */}
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Created Date Range
                </label>
                <div className="flex gap-2">
                  <DatePicker
                    selected={filters.dateRange.startDate}
                    onChange={(date) => setFilters({...filters, dateRange: {...filters.dateRange, startDate: date}})}
                    selectsStart
                    startDate={filters.dateRange.startDate}
                    endDate={filters.dateRange.endDate}
                    placeholderText="Start Date"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                    dateFormat="MMM dd, yyyy"
                  />
                  <DatePicker
                    selected={filters.dateRange.endDate}
                    onChange={(date) => setFilters({...filters, dateRange: {...filters.dateRange, endDate: date}})}
                    selectsEnd
                    startDate={filters.dateRange.startDate}
                    endDate={filters.dateRange.endDate}
                    minDate={filters.dateRange.startDate}
                    placeholderText="End Date"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                    dateFormat="MMM dd, yyyy"
                  />
                </div>
              </div>
              
              {/* Employee Count Filter */}
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Min Employees
                  </label>
                  <input
                    type="number"
                    value={filters.minEmployees}
                    onChange={(e) => setFilters({...filters, minEmployees: e.target.value})}
                    placeholder="Min"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                    min="0"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Max Employees
                  </label>
                  <input
                    type="number"
                    value={filters.maxEmployees}
                    onChange={(e) => setFilters({...filters, maxEmployees: e.target.value})}
                    placeholder="Max"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                    min="0"
                  />
                </div>
              </div>
              
              {/* Sort Options */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Sort By
                </label>
                <div className="flex gap-2">
                  <select
                    value={filters.sortBy}
                    onChange={(e) => setFilters({...filters, sortBy: e.target.value})}
                    className="flex-1 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                  >
                    <option value="created_at">Date Created</option>
                    <option value="name">Name</option>
                    <option value="employeeCount">Employee Count</option>
                    <option value="status">Status</option>
                  </select>
                  <button
                    onClick={() => setFilters({...filters, sortOrder: filters.sortOrder === 'asc' ? 'desc' : 'asc'})}
                    className="px-3 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 transition-colors"
                  >
                    {filters.sortOrder === 'asc' ? <SortAsc className="w-4 h-4" /> : <SortDesc className="w-4 h-4" />}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Departments Table */}
      {loading && !refreshing ? (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      ) : filteredDepartments.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
          <Building className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-2">
            {searchTerm ? 'No departments found' : 'No departments yet'}
          </h3>
          <p className="text-slate-600 mb-4">
            {searchTerm 
              ? 'Try adjusting your search terms or filters'
              : user.role === 'admin' 
                ? 'Create your first department to get started'
                : 'No departments have been created yet'
            }
          </p>
          {user.role === 'admin' && !searchTerm && (
            <button
              onClick={() => handleOpenModal()}
              className="bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 mx-auto transition-colors"
            >
              <Plus className="w-4 h-4" />
              Create Department
            </button>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          {/* Table Header */}
          <div className="px-6 py-4 border-b border-slate-200 bg-slate-50">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-slate-900">
                Departments ({filteredDepartments.length})
              </h3>
              <div className="text-sm text-slate-500">
                Page {currentPage} of {totalPages}
              </div>
            </div>
          </div>
          
          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Department Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Employees
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Created By
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Created Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {paginatedDepartments.map((department) => (
                  <tr key={department.id} className="hover:bg-slate-50 transition-colors">
                    <td className="px-6 py-4">
                      <div>
                        <div className="font-medium text-slate-900">{department.name}</div>
                        {department.description && (
                          <div className="text-sm text-slate-500 mt-1 line-clamp-1">
                            {department.description}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={department.status} />
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <Users className="w-4 h-4 text-slate-400" />
                        <span className="font-medium">{department.employeeCount || 0}</span>
                        <span className="text-sm text-slate-500">employees</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-slate-900">
                        {department.created_by_details?.full_name || 'System'}
                      </div>
                      <div className="text-xs text-slate-500">
                        {department.created_by_details?.role || ''}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-slate-900">
                        {formatDate(department.created_at)}
                      </div>
                      {department.updated_at !== department.created_at && (
                        <div className="text-xs text-slate-500">
                          Updated: {formatDate(department.updated_at)}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleOpenDetailsModal(department)}
                          className="p-2 hover:bg-sky-50 hover:text-sky-700 rounded-md transition-colors"
                          title="View details"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        
                        {user.role === 'admin' && (
                          <>
                            <button
                              onClick={() => handleOpenModal(department)}
                              className="p-2 hover:bg-green-50 hover:text-green-700 rounded-md transition-colors"
                              title="Edit department"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDelete(department.id, department.name)}
                              className="p-2 hover:bg-red-50 hover:text-red-700 rounded-md transition-colors"
                              title="Delete department"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {/* Table Footer - Pagination */}
          {totalPages > 1 && (
            <div className="px-6 py-4 border-t border-slate-200">
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                <div className="text-sm text-slate-600">
                  Showing {(currentPage - 1) * itemsPerPage + 1} to {Math.min(currentPage * itemsPerPage, filteredDepartments.length)} of {filteredDepartments.length} departments
                </div>
                
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                    disabled={currentPage === 1}
                    className="px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                  >
                    <ChevronLeft className="w-4 h-4" />
                    Previous
                  </button>
                  
                  <div className="flex gap-1">
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
                          onClick={() => setCurrentPage(pageNum)}
                          className={`px-4 py-2 rounded-lg transition-colors ${
                            currentPage === pageNum
                              ? 'bg-gradient-to-r from-sky-600 to-indigo-600 text-white'
                              : 'border border-slate-300 hover:bg-slate-50'
                          }`}
                        >
                          {pageNum}
                        </button>
                      );
                    })}
                  </div>
                  
                  <button
                    onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                    disabled={currentPage === totalPages}
                    className="px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                  >
                    Next
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Add/Edit Department Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-md w-full mx-auto shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="mb-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-2xl font-bold text-slate-900">
                    {editingDepartment ? 'Edit Department' : 'Add New Department'}
                  </h2>
                  <button
                    onClick={handleCloseModal}
                    className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
                <p className="text-sm text-slate-600 mt-1">
                  {editingDepartment ? 'Update department information' : 'Create a new department in the system'}
                </p>
              </div>
              
              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-slate-700 mb-2">
                    Department Name *
                  </label>
                  <input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    placeholder="e.g., Technology Department"
                    className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all ${
                      formErrors.name ? 'border-red-300' : 'border-slate-300'
                    }`}
                    disabled={loading}
                  />
                  {formErrors.name && (
                    <p className="mt-1 text-sm text-red-600">{formErrors.name}</p>
                  )}
                </div>
                
                <div>
                  <label htmlFor="description" className="block text-sm font-medium text-slate-700 mb-2">
                    Description
                  </label>
                  <textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    placeholder="Brief description of the department's purpose and responsibilities"
                    rows={3}
                    className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all ${
                      formErrors.description ? 'border-red-300' : 'border-slate-300'
                    }`}
                    disabled={loading}
                  />
                  {formErrors.description && (
                    <p className="mt-1 text-sm text-red-600">{formErrors.description}</p>
                  )}
                  <div className="mt-1 text-xs text-slate-500 flex justify-between">
                    <span>{formData.description.length}/500 characters</span>
                    <span>{500 - formData.description.length} remaining</span>
                  </div>
                </div>
                
                <div>
                  <label htmlFor="status" className="block text-sm font-medium text-slate-700 mb-2">
                    Status
                  </label>
                  <select
                    id="status"
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
                    disabled={loading}
                  >
                    <option value="active">Active</option>
                    <option value="inactive">Inactive</option>
                  </select>
                  <p className="mt-1 text-xs text-slate-500">
                    Active departments are visible and can be assigned to users
                  </p>
                </div>
                
                <div className="flex justify-end gap-3 pt-4 border-t border-slate-200">
                  <button
                    type="button"
                    onClick={handleCloseModal}
                    disabled={loading}
                    className="px-5 py-2.5 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="px-5 py-2.5 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                  >
                    {loading ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        {editingDepartment ? 'Updating...' : 'Creating...'}
                      </>
                    ) : (
                      <>
                        {editingDepartment ? 'Update Department' : 'Create Department'}
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}

      {/* Department Details Modal */}
      {isDetailsModalOpen && selectedDepartment && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl w-full max-w-6xl mx-auto shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              {/* Modal Header */}
              <div className="mb-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Building className="w-8 h-8 text-indigo-600" />
                    <div>
                      <h2 className="text-2xl font-bold text-slate-900">
                        {selectedDepartment.name}
                      </h2>
                      <div className="flex items-center gap-3 mt-1">
                        <StatusBadge status={selectedDepartment.status} />
                        <span className="text-sm text-slate-500">
                          Created {formatDate(selectedDepartment.created_at)}
                        </span>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={handleCloseDetailsModal}
                    className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
                
                {selectedDepartment.description && (
                  <p className="mt-4 text-slate-600 bg-slate-50 p-4 rounded-lg">
                    {selectedDepartment.description}
                  </p>
                )}
              </div>
              
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Department Information */}
                <div className="lg:col-span-1">
                  <div className="bg-slate-50 rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-slate-900 mb-4">Department Information</h3>
                    
                    <div className="space-y-4">
                      <div>
                        <div className="text-sm font-medium text-slate-500">Total Employees</div>
                        <div className="text-2xl font-bold text-slate-900 mt-1">
                          {selectedDepartment.employeeCount || 0}
                        </div>
                      </div>
                      
                      <div>
                        <div className="text-sm font-medium text-slate-500">Created By</div>
                        <div className="mt-1">
                          <div className="font-medium text-slate-900">
                            {selectedDepartment.created_by_details?.full_name || 'System'}
                          </div>
                          <div className="text-sm text-slate-500">
                            {selectedDepartment.created_by_details?.role || ''}
                          </div>
                          {selectedDepartment.created_by_details?.work_mail_address && (
                            <div className="text-sm text-slate-500">
                              {selectedDepartment.created_by_details.work_mail_address}
                            </div>
                          )}
                        </div>
                      </div>
                      
                      <div>
                        <div className="text-sm font-medium text-slate-500">Creation Date</div>
                        <div className="text-sm text-slate-900 mt-1">
                          {formatDate(selectedDepartment.created_at)}
                        </div>
                      </div>
                      
                      {selectedDepartment.updated_at !== selectedDepartment.created_at && (
                        <div>
                          <div className="text-sm font-medium text-slate-500">Last Updated</div>
                          <div className="text-sm text-slate-900 mt-1">
                            {formatDate(selectedDepartment.updated_at)}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                
                {/* Employees List */}
                <div className="lg:col-span-2">
                  <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
                    <div className="p-4 border-b border-slate-200 bg-slate-50">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                        <h3 className="text-lg font-semibold text-slate-900">
                          Employees ({departmentEmployees.length})
                        </h3>
                        
                        <div className="relative">
                          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                          <input
                            type="text"
                            placeholder="Search employees..."
                            value={employeeSearchTerm}
                            onChange={(e) => setEmployeeSearchTerm(e.target.value)}
                            className="w-full sm:w-64 pl-9 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all text-sm"
                          />
                        </div>
                      </div>
                    </div>
                    
                    {employeesLoading ? (
                      <div className="p-8 flex justify-center items-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                      </div>
                    ) : filteredEmployees.length === 0 ? (
                      <div className="p-8 text-center">
                        <User className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                        <h4 className="text-lg font-medium text-slate-900 mb-1">
                          {employeeSearchTerm ? 'No employees found' : 'No employees in this department'}
                        </h4>
                        <p className="text-slate-500">
                          {employeeSearchTerm 
                            ? 'Try adjusting your search terms' 
                            : 'This department currently has no assigned employees'}
                        </p>
                      </div>
                    ) : (
                      <>
                        <div className="overflow-x-auto">
                          <table className="w-full">
                            <thead className="bg-slate-50">
                              <tr>
                                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                                  Employee
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                                  Contact
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                                  Status
                                </th>
                                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">
                                  Created
                                </th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-200">
                              {paginatedEmployees.map((employee) => (
                                <tr key={employee.id} className="hover:bg-slate-50 transition-colors">
                                  <td className="px-4 py-3">
                                    <div>
                                      <div className="font-medium text-slate-900">{employee.full_name}</div>
                                      <div className="text-xs text-slate-500 mt-1">
                                        {employee.role?.toUpperCase()}
                                      </div>
                                    </div>
                                  </td>
                                  <td className="px-4 py-3">
                                    <div className="space-y-1">
                                      <div className="flex items-center gap-2 text-sm">
                                        <Mail className="w-3 h-3 text-slate-400" />
                                        <span className="text-slate-700">{employee.work_mail_address}</span>
                                      </div>
                                      <div className="flex items-center gap-2 text-sm">
                                        <Phone className="w-3 h-3 text-slate-400" />
                                        <span className="text-slate-700">{employee.phone_number}</span>
                                      </div>
                                    </div>
                                  </td>
                                  <td className="px-4 py-3">
                                    <EmployeeStatusBadge status={employee.status} />
                                  </td>
                                  <td className="px-4 py-3">
                                    <div className="text-sm text-slate-900">
                                      {formatDate(employee.created_at)}
                                    </div>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                        
                        {/* Employee Pagination */}
                        {totalEmployeePages > 1 && (
                          <div className="px-4 py-3 border-t border-slate-200">
                            <div className="flex items-center justify-between">
                              <div className="text-sm text-slate-600">
                                Showing {(employeeCurrentPage - 1) * employeesPerPage + 1} to {Math.min(employeeCurrentPage * employeesPerPage, filteredEmployees.length)} of {filteredEmployees.length} employees
                              </div>
                              <div className="flex items-center gap-2">
                                <button
                                  onClick={() => setEmployeeCurrentPage(prev => Math.max(1, prev - 1))}
                                  disabled={employeeCurrentPage === 1}
                                  className="px-3 py-1 border border-slate-300 rounded text-sm hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                  Previous
                                </button>
                                <div className="flex gap-1">
                                  {Array.from({ length: Math.min(3, totalEmployeePages) }, (_, i) => {
                                    let pageNum;
                                    if (totalEmployeePages <= 3) {
                                      pageNum = i + 1;
                                    } else if (employeeCurrentPage <= 2) {
                                      pageNum = i + 1;
                                    } else if (employeeCurrentPage >= totalEmployeePages - 1) {
                                      pageNum = totalEmployeePages - 2 + i;
                                    } else {
                                      pageNum = employeeCurrentPage - 1 + i;
                                    }
                                    
                                    return (
                                      <button
                                        key={pageNum}
                                        onClick={() => setEmployeeCurrentPage(pageNum)}
                                        className={`px-3 py-1 rounded text-sm transition-colors ${
                                          employeeCurrentPage === pageNum
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
                                  onClick={() => setEmployeeCurrentPage(prev => Math.min(totalEmployeePages, prev + 1))}
                                  disabled={employeeCurrentPage === totalEmployeePages}
                                  className="px-3 py-1 border border-slate-300 rounded text-sm hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                                >
                                  Next
                                </button>
                              </div>
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                </div>
              </div>
              
              {/* Action Buttons */}
              {user.role === 'admin' && (
                <div className="mt-6 pt-6 border-t border-slate-200 flex justify-end gap-3">
                  <button
                    onClick={() => handleOpenModal(selectedDepartment)}
                    className="px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors flex items-center gap-2"
                  >
                    <Edit2 className="w-4 h-4" />
                    Edit Department
                  </button>
                  <button
                    onClick={() => {
                      handleCloseDetailsModal();
                      handleDelete(selectedDepartment.id, selectedDepartment.name);
                    }}
                    className="px-4 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-50 transition-colors flex items-center gap-2"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete Department
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Loading Overlay */}
      {loading && (
        <div className="fixed inset-0 bg-black/10 backdrop-blur-sm z-40 flex items-center justify-center">
          <div className="bg-white p-6 rounded-xl shadow-lg flex flex-col items-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
            <p className="text-slate-700">Loading departments...</p>
          </div>
        </div>
      )}
    </div>
  );
}