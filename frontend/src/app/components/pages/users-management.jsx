/* eslint-disable react-hooks/exhaustive-deps */
/* eslint-disable no-unused-vars */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth, api } from '../../context/auth-context';
import {
  Plus,
  Search,
  Edit2,
  Trash2,
  X,
  Mail,
  User as UserIcon,
  Briefcase,
  Phone,
  Filter,
  RefreshCw,
  Shield,
  BarChart3,
  Users,
  CheckCircle,
  XCircle,
  Eye,
  Calendar,
  Key,
  Download,
  Upload,
  Clock,
  Sun,
  Moon,
  Cloud,
  ChevronDown,
  ChevronUp,
  PieChart,
  TrendingUp,
  UserCheck,
  UserX,
  AlertCircle
} from 'lucide-react';
import { toast } from 'sonner';
import { Toaster } from 'sonner';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";

export default function UsersManagement() {
  const { user: currentUser } = useAuth();
  const navigate = useNavigate();

  const [users, setUsers] = useState([]);
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState('add');
  const [selectedUser, setSelectedUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Day-off specific states
  const [showDayOffModal, setShowDayOffModal] = useState(false);
  const [dayOffMode, setDayOffMode] = useState('view'); // 'view', 'edit', 'bulk'
  const [selectedDayOffUser, setSelectedDayOffUser] = useState(null);
  const [dayOffStats, setDayOffStats] = useState(null);
  const [showDayOffStats, setShowDayOffStats] = useState(false);
  const [dayOffFormData, setDayOffFormData] = useState({
    day_off: 'none'
  });

  const [searchTerm, setSearchTerm] = useState('');
  const [activeFilters, setActiveFilters] = useState({
    role: '',
    status: '',
    department: '',
    dayOff: '',
    dateFrom: null,
    dateTo: null
  });
  const [showFilters, setShowFilters] = useState(false);

  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const [formData, setFormData] = useState({
    full_name: '',
    email: '',
    phone_number: '',
    role: 'employee',
    department: '',
    status: 'pending',
    day_off: 'none'
  });


  const [formErrors, setFormErrors] = useState({});
  const [departments, setDepartments] = useState([]);
  const [selectedDateRange, setSelectedDateRange] = useState([null, null]);
  const [startDate, endDate] = selectedDateRange;

  // Stats
  const [stats, setStats] = useState({
    totalUsers: 0,
    activeUsers: 0,
    pendingUsers: 0,
    employeeCount: 0,
    managerCount: 0,
    adminCount: 0,
    analystCount: 0,
    recentUsers: 0
  });

  // Day-off choices mapping
  const dayOffChoices = [
    { value: 'monday', label: 'Monday'},
    { value: 'tuesday', label: 'Tuesday'},
    { value: 'wednesday', label: 'Wednesday'},
    { value: 'thursday', label: 'Thursday'},
    { value: 'friday', label: 'Friday'},
    { value: 'saturday', label: 'Saturday'},
    { value: 'sunday', label: 'Sunday'},
    { value: 'none', label: 'No Day Off'}
  ];

  const getDayOffIcon = (day) => {
    const choice = dayOffChoices.find(c => c.value === day);
    return choice ? choice.icon : '📅';
  };

  const getDayOffLabel = (day) => {
    const choice = dayOffChoices.find(c => c.value === day);
    return choice ? choice.label : day || 'Not set';
  };

  // Get role-specific description
  const getDescription = () => {
    switch (currentUser?.role) {
      case 'admin':
        return 'Manage all system users, roles, departments, day-offs, and access permissions across the organization';
      case 'manager':
        return 'View and manage team members within your department. Cannot manage admin users.';
      case 'analyst':
        return 'View all users and day-off statistics for analytical purposes. Read-only access.';
      default:
        return 'User management dashboard';
    }
  };

  const pageTitle = currentUser?.role === 'analyst' ? 'User Analytics' :
    currentUser?.role === 'manager' ? 'Team Management' :
      'User Management';

  // Fetch users from API
  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await api.get('/users/');
      if (response.data && response.data.users) {
        const usersData = response.data.users;
        setUsers(usersData);
        setFilteredUsers(usersData);
        calculateStats(usersData);
      }
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error('Failed to load users. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Fetch day-off statistics
  const fetchDayOffStats = async () => {
    try {
      const response = await api.get('/day-offs/statistics/');
      if (response.data.success) {
        setDayOffStats(response.data);
      }
    } catch (error) {
      console.error('Error fetching day-off statistics:', error);
    }
  };

  // Fetch departments
  const fetchDepartments = async () => {
    try {
      const response = await api.get('/departments/all/');
      if (response.data.success) {
        setDepartments(response.data.data.filter(dept => dept.status === 'active'));
      }
    } catch (error) {
      console.error('Error fetching departments:', error);
    }
  };

  // Calculate statistics
  const calculateStats = (usersData) => {
    const totalUsers = usersData.length;
    const activeUsers = usersData.filter(u => u.status === 'approved').length;
    const pendingUsers = usersData.filter(u => u.status === 'pending').length;

    // Last 7 days users
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
    const recentUsers = usersData.filter(u => {
      const createdDate = new Date(u.created_at);
      return createdDate >= sevenDaysAgo;
    }).length;

    const roleCounts = {
      employee: 0,
      manager: 0,
      admin: 0,
      analyst: 0
    };

    usersData.forEach(user => {
      if (roleCounts[user.role] !== undefined) {
        roleCounts[user.role]++;
      }
    });

    setStats({
      totalUsers,
      activeUsers,
      pendingUsers,
      recentUsers,
      employeeCount: roleCounts.employee,
      managerCount: roleCounts.manager,
      adminCount: roleCounts.admin,
      analystCount: roleCounts.analyst
    });
  };

  // Initial fetch
  useEffect(() => {
    if (currentUser) {
      fetchUsers();
      fetchDepartments();
      if (currentUser.role === 'admin' || currentUser.role === 'manager') {
        fetchDayOffStats();
      }
    }
  }, [currentUser]);

  // Apply filters whenever dependencies change
  useEffect(() => {
    let filtered = users;

    // Apply search
    if (searchTerm.trim()) {
      filtered = filtered.filter(user =>
        user.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.work_mail_address?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.phone_number?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply role-based access control
    if (currentUser?.role === 'manager') {
      // Managers can't see admin users
      filtered = filtered.filter(user => user.role !== 'admin');
    }

    // Apply additional filters
    if (activeFilters.role) {
      filtered = filtered.filter(user => user.role === activeFilters.role);
    }

    if (activeFilters.status) {
      filtered = filtered.filter(user => user.status === activeFilters.status);
    }

    if (activeFilters.department) {
      filtered = filtered.filter(user =>
        user.department_details && user.department_details.id === parseInt(activeFilters.department)
      );
    }

    // Apply day-off filter
    if (activeFilters.dayOff) {
      if (activeFilters.dayOff === 'none') {
        filtered = filtered.filter(user => !user.day_off || user.day_off === 'none');
      } else {
        filtered = filtered.filter(user => user.day_off === activeFilters.dayOff);
      }
    }

    // Apply date range filter
    if (activeFilters.dateFrom) {
      filtered = filtered.filter(user => {
        const userDate = new Date(user.created_at);
        return userDate >= new Date(activeFilters.dateFrom);
      });
    }

    if (activeFilters.dateTo) {
      filtered = filtered.filter(user => {
        const userDate = new Date(user.created_at);
        // Set to end of day for dateTo filter
        const dateTo = new Date(activeFilters.dateTo);
        dateTo.setHours(23, 59, 59, 999);
        return userDate <= dateTo;
      });
    }

    setFilteredUsers(filtered);
    setCurrentPage(1); // Reset to first page when filters change
  }, [searchTerm, activeFilters, users, currentUser]);

  // Handle date range change
  const handleDateRangeChange = (dates) => {
    const [start, end] = dates;
    setSelectedDateRange(dates);

    if (start && end) {
      setActiveFilters(prev => ({
        ...prev,
        dateFrom: start.toISOString().split('T')[0],
        dateTo: end.toISOString().split('T')[0]
      }));
    } else if (start && !end) {
      setActiveFilters(prev => ({
        ...prev,
        dateFrom: start.toISOString().split('T')[0],
        dateTo: null
      }));
    } else {
      setActiveFilters(prev => ({
        ...prev,
        dateFrom: null,
        dateTo: null
      }));
    }
  };

  // Check user permissions
  const canViewUser = (targetUser) => {
    if (!currentUser || !targetUser) return false;

    switch (currentUser.role) {
      case 'admin':
        return true; // Admin can see everyone
      case 'manager':
        return targetUser.role !== 'admin'; // Managers can't see admin users
      case 'analyst':
        return true; // Analysts can see everyone
      default:
        return false;
    }
  };

  const canEditUser = (targetUser) => {
    if (!currentUser || !targetUser) return false;

    switch (currentUser.role) {
      case 'admin':
        return true; // Admin can edit everyone
      case 'manager':
        // Managers can edit employees in their department
        if (targetUser.role === 'employee') {
          return currentUser.department === targetUser.department;
        }
        return false;
      case 'analyst':
        return false; // Analysts can't edit anyone
      default:
        return false;
    }
  };

  const canManageDayOff = (targetUser) => {
    if (!currentUser || !targetUser) return false;

    switch (currentUser.role) {
      case 'admin':
        return true; // Admin can manage everyone's day-off
      case 'manager':
        // Managers can manage day-off for employees in their department
        if (targetUser.role === 'employee') {
          return currentUser.department === targetUser.department;
        }
        return false;
      case 'analyst':
        return false; // Analysts can't manage day-off
      default:
        return false;
    }
  };

  const canDeleteUser = (targetUser) => {
    if (!currentUser || !targetUser) return false;

    switch (currentUser.role) {
      case 'admin':
        // Admin can delete anyone except themselves
        return currentUser.id !== targetUser.id;
      case 'manager':
        // Managers can only delete employees in their department
        if (targetUser.role === 'employee' && currentUser.department === targetUser.department) {
          return currentUser.id !== targetUser.id;
        }
        return false;
      default:
        return false;
    }
  };

  const handleAddUser = () => {
    if (currentUser?.role !== 'admin' && currentUser?.role !== 'manager') {
      toast.error('You do not have permission to add users');
      return;
    }

    setModalMode('add');
    setFormData({
      full_name: '',
      email: '',
      phone_number: '',
      role: 'employee',
      department: '',
      status: 'pending'
    });
    setFormErrors({});
    setShowModal(true);
  };

  const handleEditUser = (user) => {
    if (!canEditUser(user)) {
      toast.error('You do not have permission to edit this user');
      return;
    }

    setModalMode('edit');
    setSelectedUser(user);
    setFormData({
      full_name: user.full_name,
      email: user.email,
      phone_number: user.phone_number,
      role: user.role,
      department: user.department || '',
      status: user.status,
      day_off: user.day_off || 'none'  // Add this line
    });
    setFormErrors({});
    setShowModal(true);
  };

  // Day-off management handlers
  const handleViewDayOff = (user) => {
    setDayOffMode('view');
    setSelectedDayOffUser(user);
    setDayOffFormData({ day_off: user.day_off || 'none' });
    setShowDayOffModal(true);
  };

  const handleEditDayOff = (user) => {
    if (!canManageDayOff(user)) {
      toast.error('You do not have permission to manage this user\'s day-off');
      return;
    }

    setDayOffMode('edit');
    setSelectedDayOffUser(user);
    setDayOffFormData({ day_off: user.day_off || 'none' });
    setShowDayOffModal(true);
  };

  const handleUpdateMyDayOff = async () => {
    try {
      const response = await api.put('/my-day-off/update/', dayOffFormData);
      if (response.data.success) {
        toast.success('Your day-off has been updated successfully');
        setShowDayOffModal(false);
        fetchUsers(); // Refresh users to get updated day-off
        if (currentUser.role === 'admin' || currentUser.role === 'manager') {
          fetchDayOffStats();
        }
      }
    } catch (error) {
      console.error('Error updating day-off:', error);
      toast.error(error.response?.data?.message || 'Failed to update day-off');
    }
  };

  const handleUpdateUserDayOff = async () => {
    if (!selectedDayOffUser) return;

    try {
      const response = await api.put(`/user/${selectedDayOffUser.id}/day-off/update/`, dayOffFormData);
      if (response.data.success) {
        toast.success(`Day-off updated successfully for ${selectedDayOffUser.full_name}`);
        setShowDayOffModal(false);
        fetchUsers(); // Refresh users to get updated day-off
        fetchDayOffStats();
      }
    } catch (error) {
      console.error('Error updating user day-off:', error);
      toast.error(error.response?.data?.message || 'Failed to update day-off');
    }
  };

  const handleClearMyDayOff = async () => {
    if (!confirm('Are you sure you want to clear your day-off?')) return;

    try {
      const response = await api.delete('/my-day-off/clear/');
      if (response.data.success) {
        toast.success('Your day-off has been cleared');
        fetchUsers();
        if (currentUser.role === 'admin' || currentUser.role === 'manager') {
          fetchDayOffStats();
        }
      }
    } catch (error) {
      console.error('Error clearing day-off:', error);
      toast.error(error.response?.data?.message || 'Failed to clear day-off');
    }
  };

  const handleClearUserDayOff = async (user) => {
    if (!canManageDayOff(user)) {
      toast.error('You do not have permission to clear this user\'s day-off');
      return;
    }

    if (!confirm(`Are you sure you want to clear day-off for ${user.full_name}?`)) return;

    try {
      const response = await api.delete(`/user/${user.id}/day-off/clear/`);
      if (response.data.success) {
        toast.success(`Day-off cleared successfully for ${user.full_name}`);
        fetchUsers();
        fetchDayOffStats();
      }
    } catch (error) {
      console.error('Error clearing user day-off:', error);
      toast.error(error.response?.data?.message || 'Failed to clear day-off');
    }
  };

  const handleBulkDayOffUpdate = async () => {
    // This would be implemented for bulk operations
    toast.info('Bulk day-off update feature coming soon');
  };

  const handleDeleteUser = async (user) => {
    if (!canDeleteUser(user)) {
      toast.error('You do not have permission to delete this user');
      return;
    }

    if (!confirm(`Are you sure you want to delete user "${user.full_name}"? This action cannot be undone.`)) {
      return;
    }

    try {
      setLoading(true);
      const response = await api.delete(`/users/${user.id}/delete/`);
      if (response.data.message) {
        toast.success('User deleted successfully');
        fetchUsers();
        fetchDayOffStats();
      }
    } catch (error) {
      console.error('Error deleting user:', error);
      toast.error(error.response?.data?.error || 'Failed to delete user');
    } finally {
      setLoading(false);
    }
  };

  const handleActivateUser = async (userId) => {
    try {
      const response = await api.put(`/users/${userId}/activate/`);
      if (response.data.message) {
        toast.success('User activated successfully');
        fetchUsers();
      }
    } catch (error) {
      console.error('Error activating user:', error);
      toast.error(error.response?.data?.error || 'Failed to activate user');
    }
  };

  const handleDeactivateUser = async (userId) => {
    try {
      const response = await api.put(`/users/${userId}/deactivate/`);
      if (response.data.message) {
        toast.success('User deactivated successfully');
        fetchUsers();
      }
    } catch (error) {
      console.error('Error deactivating user:', error);
      toast.error(error.response?.data?.error || 'Failed to deactivate user');
    }
  };

  const handleResetPassword = async (userId) => {
    if (!confirm('Send password reset link to this user?')) {
      return;
    }

    try {
      // First get user's work email
      const user = users.find(u => u.id === userId);
      if (!user || !user.work_mail_address) {
        toast.error('User work email not found');
        return;
      }

      // Call password reset OTP endpoint
      const response = await api.post('/auth/password-reset/request-otp/', {
        work_mail_address: user.work_mail_address
      });

      if (response.data.message) {
        toast.success('Password reset link sent to user\'s email');
      }
    } catch (error) {
      console.error('Error resetting password:', error);
      toast.error(error.response?.data?.error || 'Failed to reset password');
    }
  };

  const validateForm = () => {
    const errors = {};

    if (!formData.full_name.trim()) {
      errors.full_name = 'Full name is required';
    }

    if (!formData.email.trim()) {
      errors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      errors.email = 'Email is invalid';
    }

    if (!formData.phone_number.trim()) {
      errors.phone_number = 'Phone number is required';
    } else if (!/^\+[1-9]\d{1,14}$/.test(formData.phone_number)) {
      errors.phone_number = 'Phone number must be in international format (e.g., +250123456789)';
    }

    if (formData.role === 'employee' && !formData.department) {
      errors.department = 'Department is required for employees';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      let response;

      // Prepare data without password fields
      const userData = {
        full_name: formData.full_name,
        email: formData.email,
        phone_number: formData.phone_number,
        role: formData.role,
        department: formData.department || null,
        status: formData.status
      };

      if (modalMode === 'add') {
        response = await api.post('/users/', userData);
        if (response.data.message) {
          toast.success('User created successfully. Password will be auto-generated and sent to email.');
        }
      } else {
        response = await api.put(`/users/${selectedUser.id}/update/`, userData);
        if (response.data.message) {
          toast.success('User updated successfully');
        }
      }

      setShowModal(false);
      fetchUsers();
      fetchDayOffStats();
    } catch (error) {
      console.error('Error saving user:', error);

      if (error.response?.data?.errors) {
        setFormErrors(error.response.data.errors);
      } else if (error.response?.data?.error) {
        toast.error(error.response.data.error);
      } else {
        toast.error('Failed to save user. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchUsers();
    if (currentUser.role === 'admin' || currentUser.role === 'manager') {
      fetchDayOffStats();
    }
  };

  const handleClearFilters = () => {
    setActiveFilters({
      role: '',
      status: '',
      department: '',
      dayOff: '',
      dateFrom: null,
      dateTo: null
    });
    setSelectedDateRange([null, null]);
    setSearchTerm('');
  };

  // Export users to CSV with day-off information
  const handleExportUsers = () => {
    const csvContent = [
      ['Name', 'Email', 'Work Email', 'Phone', 'Role', 'Department', 'Status', 'Day Off', 'Created Date'],
      ...filteredUsers.map(user => [
        user.full_name,
        user.email,
        user.work_mail_address,
        user.phone_number,
        user.role,
        user.department_details?.name || 'N/A',
        user.status,
        getDayOffLabel(user.day_off),
        new Date(user.created_at).toLocaleDateString()
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `users_${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);

    toast.success('Users exported successfully');
  };

  // Pagination
  const totalPages = Math.ceil(filteredUsers.length / itemsPerPage);
  const paginatedUsers = filteredUsers.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // Role badge colors
  const getRoleColor = (role) => {
    switch (role) {
      case 'admin': return 'bg-purple-100 text-purple-800';
      case 'manager': return 'bg-blue-100 text-blue-800';
      case 'analyst': return 'bg-teal-100 text-teal-800';
      case 'employee': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Status badge colors
  const getStatusColor = (status) => {
    switch (status) {
      case 'approved': return 'bg-emerald-100 text-emerald-700';
      case 'pending': return 'bg-amber-100 text-amber-700';
      case 'rejected': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  // Day-off badge colors
  const getDayOffColor = (day) => {
    switch (day) {
      case 'monday':
      case 'tuesday':
      case 'wednesday':
      case 'thursday':
      case 'friday':
        return 'bg-indigo-100 text-indigo-700';
      case 'saturday':
      case 'sunday':
        return 'bg-amber-100 text-amber-700';
      case 'none':
        return 'bg-slate-100 text-slate-600';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  };

  // Format date
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  // Get role display name
  const getRoleDisplayName = (role) => {
    const roleNames = {
      admin: 'Admin',
      manager: 'Manager',
      analyst: 'Analyst',
      employee: 'Employee'
    };
    return roleNames[role] || role;
  };

  // Get status display name
  const getStatusDisplayName = (status) => {
    const statusNames = {
      approved: 'Active',
      pending: 'Pending',
      rejected: 'Rejected'
    };
    return statusNames[status] || status;
  };

  // If no permission, show access denied
  if (!currentUser || (currentUser.role !== 'admin' && currentUser.role !== 'manager' && currentUser.role !== 'analyst')) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Shield className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Access Denied</h2>
          <p className="text-slate-600">You don't have permission to access this page.</p>
          <button
            onClick={() => navigate('/dashboard')}
            className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Toaster position="top-right" richColors />

      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <Users className="w-8 h-8 text-indigo-600" />
            <h1 className="text-3xl font-bold text-slate-900">{pageTitle}</h1>
          </div>
          <p className="text-slate-600">{getDescription()}</p>
        </div>

        <div className="flex items-center gap-3">
          {(currentUser.role === 'admin' || currentUser.role === 'manager') && (
            <button
              onClick={() => {
                setShowDayOffStats(!showDayOffStats);
                if (!dayOffStats) fetchDayOffStats();
              }}
              className="px-3 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 flex items-center gap-2"
              title="View Day-Off Statistics"
            >
              <PieChart className="w-4 h-4" />
              Day-Off Stats
            </button>
          )}

          {/* {currentUser.role === 'admin' && (
            <button
              onClick={handleExportUsers}
              className="px-3 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 flex items-center gap-2"
              title="Export to CSV"
            >
              <Download className="w-4 h-4" />
              Export
            </button>
          )} */}

          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="px-3 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>

          {(currentUser.role === 'admin' || currentUser.role === 'manager') && (
            <button
              onClick={handleAddUser}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Plus className="w-5 h-5" />
              Add User
            </button>
          )}
        </div>
      </div>

      {/* Day-Off Statistics Panel */}
      {showDayOffStats && dayOffStats && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <Calendar className="w-6 h-6 text-indigo-600" />
              <h2 className="text-lg font-semibold text-slate-900">Day-Off Distribution</h2>
            </div>
            <button
              onClick={() => setShowDayOffStats(false)}
              className="p-1 hover:bg-slate-100 rounded"
            >
              <X className="w-5 h-5 text-slate-500" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <div className="bg-indigo-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-indigo-700">{dayOffStats.total_users}</div>
              <div className="text-sm text-indigo-600">Total Users</div>
            </div>
            <div className="bg-emerald-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-emerald-700">
                {Object.values(dayOffStats.day_distribution).filter(d => d.count > 0 && d.display !== 'No Day Off').reduce((a, b) => a + b.count, 0)}
              </div>
              <div className="text-sm text-emerald-600">Users with Day-Off</div>
            </div>
            <div className="bg-amber-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-amber-700">
                {dayOffStats.day_distribution?.none?.count || 0}
              </div>
              <div className="text-sm text-amber-600">No Day-Off Set</div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-purple-700">
                {Object.keys(dayOffStats.role_statistics || {}).length}
              </div>
              <div className="text-sm text-purple-600">Roles with Day-Off</div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Day Distribution Chart */}
            <div>
              <h3 className="text-sm font-medium text-slate-700 mb-3">By Day</h3>
              <div className="space-y-2">
                {dayOffChoices.map(choice => {
                  const stats = dayOffStats.day_distribution?.[choice.value] || { count: 0, percentage: 0 };
                  if (choice.value === 'none') return null;
                  return (
                    <div key={choice.value} className="flex items-center gap-2">
                      <span className="w-24 text-sm text-slate-600">{choice.label}</span>
                      <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-indigo-500 rounded-full"
                          style={{ width: `${stats.percentage}%` }}
                        />
                      </div>
                      <span className="text-sm text-slate-600 w-16">{stats.count} ({stats.percentage}%)</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Role Distribution */}
            <div>
              <h3 className="text-sm font-medium text-slate-700 mb-3">By Role</h3>
              <div className="space-y-4">
                {Object.entries(dayOffStats.role_statistics || {}).map(([role, data]) => (
                  <div key={role} className="border border-slate-200 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-slate-900 capitalize">{role}</span>
                      <span className="text-sm text-slate-600">Total: {data.total}</span>
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      {Object.entries(data.day_distribution).map(([day, dayData]) => (
                        dayData.count > 0 && (
                          <div key={day} className="text-xs">
                            <span className="text-slate-500">{getDayOffLabel(day)}:</span>
                            <span className="ml-1 font-medium">{dayData.count} ({dayData.percentage}%)</span>
                          </div>
                        )
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <Users className="w-8 h-8 text-indigo-500" />
            <div className="text-2xl font-bold text-slate-900">{stats.totalUsers}</div>
          </div>
          <h3 className="text-sm font-medium text-slate-600">Total Users</h3>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <CheckCircle className="w-8 h-8 text-emerald-500" />
            <div className="text-2xl font-bold text-slate-900">{stats.activeUsers}</div>
          </div>
          <h3 className="text-sm font-medium text-slate-600">Active Users</h3>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <BarChart3 className="w-8 h-8 text-amber-500" />
            <div className="text-2xl font-bold text-slate-900">{stats.pendingUsers}</div>
          </div>
          <h3 className="text-sm font-medium text-slate-600">Pending Approval</h3>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <Calendar className="w-8 h-8 text-purple-500" />
            <div className="text-2xl font-bold text-slate-900">{stats.recentUsers}</div>
          </div>
          <h3 className="text-sm font-medium text-slate-600">Last 7 Days</h3>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex flex-col md:flex-row gap-4 mb-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by name, email, phone, or work email..."
              className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all"
            />
          </div>

          <button
            onClick={() => setShowFilters(!showFilters)}
            className="px-4 py-3 border border-slate-300 rounded-lg hover:bg-slate-50 flex items-center gap-2"
          >
            <Filter className="w-5 h-5" />
            Filters
            {(activeFilters.role || activeFilters.status || activeFilters.department || activeFilters.dayOff || activeFilters.dateFrom || activeFilters.dateTo) && (
              <span className="w-2 h-2 bg-red-500 rounded-full"></span>
            )}
          </button>
        </div>

        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-4 p-4 border border-slate-200 rounded-lg bg-slate-50">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Role</label>
              <select
                value={activeFilters.role}
                onChange={(e) => setActiveFilters({ ...activeFilters, role: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
              >
                <option value="">All Roles</option>
                <option value="admin">Admin</option>
                <option value="manager">Manager</option>
                <option value="analyst">Analyst</option>
                <option value="employee">Employee</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Status</label>
              <select
                value={activeFilters.status}
                onChange={(e) => setActiveFilters({ ...activeFilters, status: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
              >
                <option value="">All Status</option>
                <option value="approved">Active</option>
                <option value="pending">Pending</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Department</label>
              <select
                value={activeFilters.department}
                onChange={(e) => setActiveFilters({ ...activeFilters, department: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
              >
                <option value="">All Departments</option>
                {departments.map(dept => (
                  <option key={dept.id} value={dept.id}>{dept.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">Day Off</label>
              <select
                value={activeFilters.dayOff}
                onChange={(e) => setActiveFilters({ ...activeFilters, dayOff: e.target.value })}
                className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
              >
                <option value="">All Days</option>
                <option value="none">No Day Off</option>
                {dayOffChoices.filter(c => c.value !== 'none').map(choice => (
                  <option key={choice.value} value={choice.value}>{choice.label}</option>
                ))}
              </select>
            </div>

            <div className="md:col-span-4">
              <label className="block text-sm font-medium text-slate-700 mb-2">Created Date Range</label>
              <div className="relative">
                <DatePicker
                  selectsRange={true}
                  startDate={startDate}
                  endDate={endDate}
                  onChange={handleDateRangeChange}
                  isClearable={true}
                  placeholderText="Select date range"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                />
                <Calendar className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400 pointer-events-none" />
              </div>
            </div>

            {(activeFilters.role || activeFilters.status || activeFilters.department || activeFilters.dayOff || activeFilters.dateFrom || activeFilters.dateTo) && (
              <div className="md:col-span-4 flex justify-end">
                <button
                  onClick={handleClearFilters}
                  className="px-4 py-2 text-sm text-red-600 hover:text-red-700 flex items-center gap-2"
                >
                  <X className="w-4 h-4" />
                  Clear All Filters
                </button>
              </div>
            )}
          </div>
        )}

        <div className="mt-2 text-sm text-slate-500 flex flex-wrap items-center gap-2">
          <span>Showing {filteredUsers.length} of {users.length} users</span>
          {searchTerm && <span className="px-2 py-1 bg-slate-100 rounded">Search: "{searchTerm}"</span>}
          {activeFilters.role && <span className="px-2 py-1 bg-slate-100 rounded">Role: {activeFilters.role}</span>}
          {activeFilters.status && <span className="px-2 py-1 bg-slate-100 rounded">Status: {activeFilters.status}</span>}
          {activeFilters.department && (
            <span className="px-2 py-1 bg-slate-100 rounded">
              Department: {departments.find(d => d.id == activeFilters.department)?.name}
            </span>
          )}
          {activeFilters.dayOff && (
            <span className="px-2 py-1 bg-slate-100 rounded">
              Day Off: {getDayOffLabel(activeFilters.dayOff)}
            </span>
          )}
          {(activeFilters.dateFrom || activeFilters.dateTo) && (
            <span className="px-2 py-1 bg-slate-100 rounded">
              Date: {activeFilters.dateFrom || 'Any'} to {activeFilters.dateTo || 'Now'}
            </span>
          )}
        </div>
      </div>

      {/* Users Table */}
      {loading && !refreshing ? (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      ) : filteredUsers.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 p-8 text-center">
          <Users className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-2">
            {searchTerm || Object.values(activeFilters).some(f => f)
              ? 'No users found'
              : 'No users yet'}
          </h3>
          <p className="text-slate-600 mb-4">
            {searchTerm || Object.values(activeFilters).some(f => f)
              ? 'Try adjusting your search or filters'
              : 'Create your first user to get started'}
          </p>
          {(currentUser.role === 'admin' || currentUser.role === 'manager') && !searchTerm && (
            <button
              onClick={handleAddUser}
              className="bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 mx-auto"
            >
              <Plus className="w-4 h-4" />
              Add First User
            </button>
          )}
        </div>
      ) : (
        <>
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">User Details</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">Role</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">Department</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">Day Off</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">Created</th>
                    {(currentUser.role === 'admin' || currentUser.role === 'manager' || currentUser.role === 'analyst') && (
                      <th className="px-6 py-3 text-left text-xs font-medium text-slate-600 uppercase tracking-wider">Actions</th>
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {paginatedUsers.map((user) => {
                    if (!canViewUser(user)) return null;

                    return (
                      <tr key={user.id} className="hover:bg-slate-50">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-indigo-100 rounded-full flex items-center justify-center">
                              <UserIcon className="w-5 h-5 text-indigo-600" />
                            </div>
                            <div>
                              <div className="font-medium text-slate-900">{user.full_name}</div>
                              <div className="text-sm text-slate-500 flex flex-col">
                                <span className="flex items-center gap-1">
                                  <Mail className="w-3 h-3" />
                                  {user.work_mail_address}
                                </span>
                                <span className="flex items-center gap-1">
                                  <Phone className="w-3 h-3" />
                                  {user.phone_number}
                                </span>
                              </div>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-3 py-1 text-xs font-medium rounded-full ${getRoleColor(user.role)}`}>
                            {getRoleDisplayName(user.role)}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <Briefcase className="w-4 h-4 text-slate-400" />
                            <span className="text-slate-700">
                              {user.department_details?.name || 'No department'}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <span className={`px-3 py-1 text-xs font-medium rounded-full ${getDayOffColor(user.day_off)}`}>
                              <span className="mr-1">{getDayOffIcon(user.day_off)}</span>
                              {getDayOffLabel(user.day_off)}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <span className={`px-3 py-1 text-xs font-medium rounded-full ${getStatusColor(user.status)}`}>
                              {getStatusDisplayName(user.status)}
                            </span>
                            {user.status === 'pending' && (currentUser.role === 'admin' || (currentUser.role === 'manager' && user.role !== 'admin')) && (
                              <button
                                onClick={() => handleActivateUser(user.id)}
                                className="text-xs text-emerald-600 hover:text-emerald-700"
                                title="Approve user"
                              >
                                <CheckCircle className="w-4 h-4" />
                              </button>
                            )}
                            {user.status === 'approved' && canDeleteUser(user) && (
                              <button
                                onClick={() => handleDeactivateUser(user.id)}
                                className="text-xs text-red-600 hover:text-red-700"
                                title="Deactivate user"
                              >
                                <XCircle className="w-4 h-4" />
                              </button>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4 text-slate-700">
                          {formatDate(user.created_at)}
                          {user.created_by_name && (
                            <div className="text-xs text-slate-500">by {user.created_by_name}</div>
                          )}
                        </td>

                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            {/* Day-off actions - available to all authenticated users */}
                            {currentUser.id === user.id ? (
                              // User can manage their own day-off
                              <button
                                onClick={() => handleViewDayOff(user)}
                                className="p-2 hover:bg-indigo-50 rounded-lg transition-colors"
                                title="View my day-off"
                              >
                                <Calendar className="w-4 h-4 text-indigo-600" />
                              </button>
                            ) : canManageDayOff(user) ? (
                              // Admin/Manager can manage others' day-off
                              <button
                                onClick={() => handleEditDayOff(user)}
                                className="p-2 hover:bg-indigo-50 rounded-lg transition-colors"
                                title="Manage day-off"
                              >
                                <Calendar className="w-4 h-4 text-indigo-600" />
                              </button>
                            ) : currentUser.role === 'analyst' ? (
                              // Analyst can only view
                              <button
                                onClick={() => handleViewDayOff(user)}
                                className="p-2 hover:bg-indigo-50 rounded-lg transition-colors"
                                title="View day-off"
                              >
                                <Eye className="w-4 h-4 text-indigo-600" />
                              </button>
                            ) : null}

                            {canEditUser(user) && (
                              <button
                                onClick={() => handleEditUser(user)}
                                className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                                title="Edit user"
                              >
                                <Edit2 className="w-4 h-4 text-slate-600" />
                              </button>
                            )}

                            {currentUser.role === 'admin' && (
                              <button
                                onClick={() => handleResetPassword(user.id)}
                                className="p-2 hover:bg-amber-50 rounded-lg transition-colors"
                                title="Reset password"
                              >
                                <Key className="w-4 h-4 text-amber-600" />
                              </button>
                            )}

                            {canDeleteUser(user) && (
                              <button
                                onClick={() => handleDeleteUser(user)}
                                className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                                title="Delete user"
                              >
                                <Trash2 className="w-4 h-4 text-red-600" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-6 border-t border-slate-200">
              <div className="text-sm text-slate-600">
                Showing {(currentPage - 1) * itemsPerPage + 1} to {Math.min(currentPage * itemsPerPage, filteredUsers.length)} of {filteredUsers.length} users
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                  className="px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Previous
                </button>

                <div className="flex gap-1">
                  {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className={`px-4 py-2 rounded-lg transition-colors ${currentPage === page
                          ? 'bg-gradient-to-r from-sky-600 to-indigo-600 text-white'
                          : 'border border-slate-300 hover:bg-slate-50'
                        }`}
                    >
                      {page}
                    </button>
                  ))}
                </div>

                <button
                  onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                  disabled={currentPage === totalPages}
                  className="px-4 py-2 border border-slate-300 rounded-lg hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {/* Day-Off Modal */}
      {showDayOffModal && selectedDayOffUser && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
            <div className="flex items-center justify-between p-6 border-b border-slate-200">
              <h2 className="text-xl font-bold text-slate-900">
                {dayOffMode === 'view' ? 'View Day-Off' : 'Manage Day-Off'}
              </h2>
              <button
                onClick={() => setShowDayOffModal(false)}
                className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6">
              {/* User Info */}
              <div className="bg-slate-50 p-4 rounded-lg mb-6">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-indigo-100 rounded-full flex items-center justify-center">
                    <UserIcon className="w-6 h-6 text-indigo-600" />
                  </div>
                  <div>
                    <div className="font-medium text-slate-900">{selectedDayOffUser.full_name}</div>
                    <div className="text-sm text-slate-500">{selectedDayOffUser.work_mail_address}</div>
                    <div className="text-xs text-slate-400 mt-1">
                      {getRoleDisplayName(selectedDayOffUser.role)} • {selectedDayOffUser.department_details?.name || 'No department'}
                    </div>
                  </div>
                </div>
              </div>

              {/* Current Day-Off Display */}
              {dayOffMode === 'view' ? (
                <div className="text-center py-6">
                  <div className="text-6xl mb-4">{getDayOffIcon(selectedDayOffUser.day_off)}</div>
                  <div className="text-2xl font-bold text-slate-900 mb-2">
                    {getDayOffLabel(selectedDayOffUser.day_off)}
                  </div>
                  <p className="text-slate-500">
                    {selectedDayOffUser.day_off === 'none'
                      ? 'This user has no day-off set'
                      : `This user is off on ${getDayOffLabel(selectedDayOffUser.day_off)}s`}
                  </p>
                </div>
              ) : (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Select Day Off
                    </label>
                    <select
                      value={dayOffFormData.day_off}
                      onChange={(e) => setDayOffFormData({ day_off: e.target.value })}
                      className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                    >
                      {dayOffChoices.map(choice => (
                        <option key={choice.value} value={choice.value}>
                          {choice.icon} {choice.label}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Quick Selection Buttons */}
                  <div className="grid grid-cols-4 gap-2">
                    {dayOffChoices.filter(c => c.value !== 'none').map(choice => (
                      <button
                        key={choice.value}
                        onClick={() => setDayOffFormData({ day_off: choice.value })}
                        className={`p-2 text-xs rounded-lg border transition-colors ${dayOffFormData.day_off === choice.value
                            ? 'bg-indigo-50 border-indigo-300 text-indigo-700'
                            : 'border-slate-200 hover:bg-slate-50 text-slate-600'
                          }`}
                      >
                        <div className="text-lg mb-1">{choice.icon}</div>
                        <div>{choice.label.substring(0, 3)}</div>
                      </button>
                    ))}
                  </div>

                  {dayOffFormData.day_off !== 'none' && (
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mt-4">
                      <div className="flex items-start gap-2">
                        <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
                        <div className="text-sm text-amber-700">
                          <p className="font-medium mb-1">Important Note:</p>
                          <p>Setting day-off to {getDayOffLabel(dayOffFormData.day_off)} means this user will be off every {getDayOffLabel(dayOffFormData.day_off)}. Task assignments will not be scheduled on this day.</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Clear Option */}
                  {selectedDayOffUser.day_off && selectedDayOffUser.day_off !== 'none' && (
                    <div className="pt-4 border-t border-slate-200">
                      <button
                        onClick={() => currentUser.id === selectedDayOffUser.id
                          ? handleClearMyDayOff()
                          : handleClearUserDayOff(selectedDayOffUser)
                        }
                        className="text-sm text-red-600 hover:text-red-700 flex items-center gap-1"
                      >
                        <Trash2 className="w-4 h-4" />
                        Clear day-off
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-3 pt-6 border-t border-slate-200 mt-6">
                <button
                  onClick={() => setShowDayOffModal(false)}
                  className="flex-1 px-4 py-3 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg transition-colors"
                >
                  Close
                </button>
                {dayOffMode === 'edit' && (
                  <button
                    onClick={currentUser.id === selectedDayOffUser.id
                      ? handleUpdateMyDayOff
                      : handleUpdateUserDayOff
                    }
                    className="flex-1 px-4 py-3 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white rounded-lg transition-colors"
                  >
                    Save Changes
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Add/Edit Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-slate-200 sticky top-0 bg-white z-10">
              <h2 className="text-xl font-bold text-slate-900">
                {modalMode === 'add' ? 'Add New User' : 'Edit User'}
              </h2>
              <button
                onClick={() => setShowModal(false)}
                className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                disabled={loading}
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
                <div className="flex items-center gap-2 mb-2">
                  <Key className="w-5 h-5 text-amber-600" />
                  <h3 className="font-medium text-amber-800">Password Information</h3>
                </div>
                <p className="text-sm text-amber-700">
                  {modalMode === 'add'
                    ? 'System will auto-generate a secure password and send it to the user\'s email.'
                    : 'User password remains unchanged. Use "Reset Password" action to generate new password.'}
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Full Name *
                </label>
                <div className="relative">
                  <UserIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input
                    type="text"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className={`w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all ${formErrors.full_name ? 'border-red-300' : 'border-slate-300'
                      }`}
                    disabled={loading}
                    placeholder="John Doe"
                  />
                </div>
                {formErrors.full_name && (
                  <p className="mt-1 text-sm text-red-600">{formErrors.full_name}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Email *
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className={`w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all ${formErrors.email ? 'border-red-300' : 'border-slate-300'
                      }`}
                    disabled={loading}
                    placeholder="user@gmail.com"
                  />
                </div>
                {formErrors.email && (
                  <p className="mt-1 text-sm text-red-600">{formErrors.email}</p>
                )}
                <p className="mt-1 text-xs text-slate-500">Must be a Gmail address</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Phone Number *
                </label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input
                    type="tel"
                    value={formData.phone_number}
                    onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                    className={`w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all ${formErrors.phone_number ? 'border-red-300' : 'border-slate-300'
                      }`}
                    disabled={loading}
                    placeholder="+250123456789"
                  />
                </div>
                {formErrors.phone_number && (
                  <p className="mt-1 text-sm text-red-600">{formErrors.phone_number}</p>
                )}
                <p className="mt-1 text-xs text-slate-500">International format starting with +</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Role *
                  </label>
                  <select
                    value={formData.role}
                    onChange={(e) => {
                      setFormData({
                        ...formData,
                        role: e.target.value,
                        department: e.target.value !== 'employee' ? '' : formData.department
                      });
                    }}
                    className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                    disabled={loading || (modalMode === 'edit' && currentUser.role === 'manager')}
                  >
                    {currentUser.role === 'admin' && (
                      <option value="admin">Admin</option>
                    )}
                    {currentUser.role === 'admin' && (
                      <option value="manager">Manager</option>
                    )}
                    <option value="analyst">Analyst</option>
                    <option value="employee">Employee</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Status
                  </label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                    disabled={loading}
                  >
                    <option value="pending">Pending</option>
                    <option value="approved">Active</option>
                    <option value="rejected">Rejected</option>
                  </select>
                </div>
              </div>

              {/* Day Off Field - New Addition */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Day Off
                </label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <select
                    value={formData.day_off || 'none'}
                    onChange={(e) => setFormData({ ...formData, day_off: e.target.value })}
                    className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none appearance-none bg-white"
                    disabled={loading}
                  >
                    {dayOffChoices.map(choice => (
                      <option key={choice.value} value={choice.value}>
                        {choice.icon} {choice.label}
                      </option>
                    ))}
                  </select>
                </div>
                <p className="mt-1 text-xs text-slate-500">
                  Select the day when this user is off work. Tasks won't be scheduled on this day.
                </p>
              </div>

              {formData.role === 'employee' && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Department *
                  </label>
                  <div className="relative">
                    <Briefcase className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                    <select
                      value={formData.department}
                      onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                      className={`w-full pl-10 pr-4 py-3 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition-all appearance-none bg-white ${formErrors.department ? 'border-red-300' : 'border-slate-300'
                        }`}
                      disabled={loading}
                    >
                      <option value="">Select a department</option>
                      {departments.map(dept => (
                        <option key={dept.id} value={dept.id}>
                          {dept.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  {formErrors.department && (
                    <p className="mt-1 text-sm text-red-600">{formErrors.department}</p>
                  )}
                </div>
              )}

              {/* Quick Day Off Selection Buttons */}
              <div className="pt-2">
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Quick Select Day Off
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {dayOffChoices.filter(c => c.value !== 'none').map(choice => (
                    <button
                      key={choice.value}
                      type="button"
                      onClick={() => setFormData({ ...formData, day_off: choice.value })}
                      className={`p-2 text-xs rounded-lg border transition-colors ${formData.day_off === choice.value
                          ? 'bg-indigo-50 border-indigo-300 text-indigo-700'
                          : 'border-slate-200 hover:bg-slate-50 text-slate-600'
                        }`}
                    >
                      <div className="text-lg mb-1">{choice.icon}</div>
                      <div>{choice.label.substring(0, 3)}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Day Off Information Message */}
              {formData.day_off && formData.day_off !== 'none' && (
                <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3">
                  <div className="flex items-start gap-2">
                    <Calendar className="w-5 h-5 text-indigo-600 flex-shrink-0 mt-0.5" />
                    <div className="text-sm text-indigo-700">
                      <p className="font-medium mb-1">Day Off Information:</p>
                      <p>This user will be off every {getDayOffLabel(formData.day_off)}.
                        Task assignments will not be scheduled on this day.</p>
                    </div>
                  </div>
                </div>
              )}

              <div className="flex gap-3 pt-6">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 px-4 py-3 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-3 bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      {modalMode === 'add' ? 'Creating...' : 'Saving...'}
                    </>
                  ) : (
                    modalMode === 'add' ? 'Create User' : 'Save Changes'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Loading Overlay */}
      {loading && (
        <div className="fixed inset-0 bg-black/10 backdrop-blur-sm z-40 flex items-center justify-center">
          <div className="bg-white p-6 rounded-xl shadow-lg flex flex-col items-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
            <p className="text-slate-700">Loading users...</p>
          </div>
        </div>
      )}
    </div>
  );
}