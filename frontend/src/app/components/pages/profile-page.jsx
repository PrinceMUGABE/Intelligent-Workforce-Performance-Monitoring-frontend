import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Mail, Phone, Briefcase, Lock, Save, Shield, CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { Toaster } from 'sonner';
import axios from 'axios';

const BASE_URL = 'http://127.0.0.1:8000';

export default function ProfilePage() {
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const [showPasswordModal, setShowPasswordModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [error, setError] = useState(null);

  const [profileData, setProfileData] = useState({
    full_name: '',
    email: '',
    phone_number: '',
    availability_status: 'active',
  });

  const [originalProfileData, setOriginalProfileData] = useState({
    full_name: '',
    email: '',
    phone_number: '',
    availability_status: 'active',
  });

  const [userDetails, setUserDetails] = useState(null);

  const [passwordData, setPasswordData] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  // Get token from localStorage
  const getToken = () => {
    return localStorage.getItem('access_token');
  };

  // Check authentication and fetch profile on mount
  useEffect(() => {
    const token = getToken();
    
    console.log('ProfilePage mounted');
    console.log('Token from localStorage:', token ? 'exists' : 'none');

    if (!token) {
      console.log('No token found, redirecting to login');
      toast.error('Please login to view your profile');
      navigate('/login');
      return;
    }

    fetchUserProfile();
  }, []);

  const fetchUserProfile = async () => {
    const token = getToken();

    if (!token) {
      console.error('No token available for profile fetch');
      setError('Authentication token is missing. Please login again.');
      setIsLoading(false);
      navigate('/login');
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      console.log('Fetching profile with token:', token.substring(0, 20) + '...');

      const response = await axios.get(`${BASE_URL}/profile/`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      console.log('Profile fetched successfully:', response.data);

      const userData = response.data;
      setUserDetails(userData);

      const profileInfo = {
        full_name: userData.full_name || '',
        email: userData.email || '',
        phone_number: userData.phone_number || '',
        availability_status: userData.availability_status || 'active',
      };

      setProfileData(profileInfo);
      setOriginalProfileData(profileInfo);

    } catch (error) {
      console.error('Error fetching profile:', error);
      console.error('Error response:', error.response?.data);
      console.error('Error status:', error.response?.status);

      if (error.response?.status === 401) {
        setError('Your session has expired. Please login again.');
        toast.error('Session expired. Please login again.');
        // Clear invalid token
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      } else {
        const errorMsg = error.response?.data?.error || 'Failed to load profile';
        setError(errorMsg);
        toast.error(errorMsg);
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    const token = getToken();

    if (!token) {
      toast.error('Session expired. Please login again.');
      navigate('/login');
      return;
    }

    try {
      setIsSaving(true);
      setError(null);

      console.log('Updating profile with data:', profileData);

      const response = await axios.put(
        `${BASE_URL}/profile/update/`,
        profileData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      console.log('Profile update response:', response.data);

      toast.success(response.data.message || 'Profile updated successfully!');
      setIsEditing(false);
      
      // Refresh user profile
      await fetchUserProfile();
    } catch (error) {
      console.error('Error updating profile:', error);
      console.error('Error response:', error.response?.data);
      
      if (error.response?.status === 401) {
        toast.error('Session expired. Please login again.');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        navigate('/login');
      } else {
        const errorMsg = error.response?.data?.error || 'Failed to update profile';
        toast.error(errorMsg);
        // Revert changes on error
        setProfileData(originalProfileData);
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();

    if (passwordData.new_password !== passwordData.confirm_password) {
      toast.error('New passwords do not match!');
      return;
    }

    if (passwordData.new_password.length < 8) {
      toast.error('Password must be at least 8 characters!');
      return;
    }

    // Validate password complexity
    const hasUpperCase = /[A-Z]/.test(passwordData.new_password);
    const hasLowerCase = /[a-z]/.test(passwordData.new_password);
    const hasNumber = /\d/.test(passwordData.new_password);
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(passwordData.new_password);

    if (!hasUpperCase || !hasLowerCase || !hasNumber || !hasSpecialChar) {
      toast.error('Password must include uppercase, lowercase, number, and special character');
      return;
    }

    const token = getToken();

    if (!token) {
      toast.error('Session expired. Please login again.');
      navigate('/login');
      return;
    }

    try {
      setIsChangingPassword(true);

      const response = await axios.put(
        `${BASE_URL}/profile/change-password/`,
        {
          current_password: passwordData.current_password,
          new_password: passwordData.new_password,
          confirm_password: passwordData.confirm_password,
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      toast.success(response.data.message || 'Password changed successfully!');
      setShowPasswordModal(false);
      setPasswordData({
        current_password: '',
        new_password: '',
        confirm_password: '',
      });

      // Logout user after password change for security
      toast.info('Please login with your new password');
      setTimeout(() => {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        navigate('/login');
      }, 2000);
    } catch (error) {
      console.error('Error changing password:', error);
      console.error('Error response:', error.response?.data);
      
      if (error.response?.status === 401) {
        toast.error('Session expired. Please login again.');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        navigate('/login');
      } else {
        toast.error(error.response?.data?.error || 'Failed to change password');
      }
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setProfileData(originalProfileData);
  };

  const getRoleBadgeColor = (role) => {
    const colors = {
      admin: 'bg-purple-100 text-purple-700',
      manager: 'bg-blue-100 text-blue-700',
      analyst: 'bg-green-100 text-green-700',
      employee: 'bg-slate-100 text-slate-700',
    };
    return colors[role] || colors.employee;
  };

  const getStatusBadge = (status) => {
    if (status === 'approved') {
      return (
        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-700">
          <CheckCircle className="w-4 h-4" />
          Approved
        </span>
      );
    } else if (status === 'pending') {
      return (
        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-700">
          <Clock className="w-4 h-4" />
          Pending
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-700">
          <XCircle className="w-4 h-4" />
          Rejected
        </span>
      );
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-slate-600">Loading profile...</p>
        </div>
      </div>
    );
  }

  if (error && !userDetails) {
    return (
      <div className="flex items-center justify-center min-h-screen p-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 max-w-md">
          <div className="flex items-start gap-3">
            <AlertCircle className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-red-800">Error Loading Profile</h3>
              <p className="text-sm text-red-700 mt-1">{error}</p>
              <button
                onClick={() => navigate('/login')}
                className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Go to Login
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!userDetails) {
    return null;
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto p-6">
      <Toaster position="top-center" richColors />

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Profile</h1>
        <p className="text-slate-600 mt-1">
          Manage your personal profile information, account settings, and security preferences
        </p>
      </div>

      {/* Profile Card */}
      <div className="bg-white p-8 rounded-xl shadow-sm border border-slate-200">
        <div className="flex items-center gap-6 mb-8">
          <div className="w-24 h-24 bg-gradient-to-br from-indigo-500 to-violet-600 rounded-full flex items-center justify-center text-white text-3xl font-bold">
            {userDetails.full_name?.charAt(0).toUpperCase() || 'U'}
          </div>
          <div>
            <h2 className="text-2xl font-bold text-slate-900">{userDetails.full_name}</h2>
            <div className="flex items-center gap-2 mt-1">
              <span className={`px-3 py-1 rounded-full text-sm font-medium capitalize ${getRoleBadgeColor(userDetails.role)}`}>
                {userDetails.role}
              </span>
              {getStatusBadge(userDetails.status)}
            </div>
            {userDetails.department_details && (
              <p className="text-sm text-slate-500 mt-2 flex items-center gap-1">
                <Briefcase className="w-4 h-4" />
                {userDetails.department_details.name}
              </p>
            )}
          </div>
        </div>

        <div className="space-y-6">
          {/* Read-only Information Section */}
          <div className="bg-slate-50 p-4 rounded-lg border border-slate-200">
            <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
              <Shield className="w-4 h-4" />
              System Information (Read-only)
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-slate-600">Work Email:</span>
                <p className="font-medium text-slate-900">{userDetails.work_mail_address}</p>
              </div>
              <div>
                <span className="text-slate-600">Role:</span>
                <p className="font-medium text-slate-900 capitalize">{userDetails.role}</p>
              </div>
              {userDetails.department_details && (
                <div>
                  <span className="text-slate-600">Department:</span>
                  <p className="font-medium text-slate-900">{userDetails.department_details.name}</p>
                </div>
              )}
              {userDetails.day_off && userDetails.day_off !== 'none' && (
                <div>
                  <span className="text-slate-600">Day Off:</span>
                  <p className="font-medium text-slate-900 capitalize">{userDetails.day_off}</p>
                </div>
              )}
              <div>
                <span className="text-slate-600">Account Status:</span>
                <p className="font-medium text-slate-900 capitalize">{userDetails.status}</p>
              </div>
              <div>
                <span className="text-slate-600">Member Since:</span>
                <p className="font-medium text-slate-900">
                  {new Date(userDetails.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          </div>

          {/* Editable Information Section */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Full Name *
              </label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  value={profileData.full_name}
                  onChange={(e) => setProfileData({ ...profileData, full_name: e.target.value })}
                  disabled={!isEditing}
                  className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none disabled:bg-slate-50 disabled:text-slate-600"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Personal Email *
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="email"
                  value={profileData.email}
                  onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                  disabled={!isEditing}
                  className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none disabled:bg-slate-50 disabled:text-slate-600"
                  required
                />
              </div>
              <p className="text-xs text-slate-500 mt-1">Only Gmail addresses allowed</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Phone Number *
              </label>
              <div className="relative">
                <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="tel"
                  value={profileData.phone_number}
                  onChange={(e) => setProfileData({ ...profileData, phone_number: e.target.value })}
                  disabled={!isEditing}
                  className="w-full pl-10 pr-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none disabled:bg-slate-50 disabled:text-slate-600"
                  placeholder="+250123456789"
                  required
                />
              </div>
              <p className="text-xs text-slate-500 mt-1">Include country code (e.g., +250)</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Availability Status
              </label>
              <select
                value={profileData.availability_status}
                onChange={(e) => setProfileData({ ...profileData, availability_status: e.target.value })}
                disabled={!isEditing}
                className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none disabled:bg-slate-50 disabled:text-slate-600"
              >
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
          </div>

          <div className="flex gap-3 pt-4">
            {!isEditing ? (
              <>
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors"
                >
                  Edit Profile
                </button>
                <button
                  onClick={() => setShowPasswordModal(true)}
                  className="px-6 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg transition-colors flex items-center gap-2"
                >
                  <Lock className="w-4 h-4" />
                  Change Password
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={handleSaveProfile}
                  disabled={isSaving}
                  className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Save className="w-4 h-4" />
                  {isSaving ? 'Saving...' : 'Save Changes'}
                </button>
                <button
                  onClick={handleCancelEdit}
                  disabled={isSaving}
                  className="px-6 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Password Change Modal */}
      {showPasswordModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-md">
            <div className="flex items-center justify-between p-6 border-b border-slate-200">
              <h2 className="text-xl font-bold text-slate-900">Change Password</h2>
              <button
                onClick={() => {
                  setShowPasswordModal(false);
                  setPasswordData({
                    current_password: '',
                    new_password: '',
                    confirm_password: '',
                  });
                }}
                className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleChangePassword} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Current Password *
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input
                    type="password"
                    value={passwordData.current_password}
                    onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                    className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  New Password *
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input
                    type="password"
                    value={passwordData.new_password}
                    onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                    className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                    required
                  />
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Must be 8+ characters with uppercase, lowercase, number, and special character
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Confirm New Password *
                </label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input
                    type="password"
                    value={passwordData.confirm_password}
                    onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                    className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                    required
                  />
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowPasswordModal(false);
                    setPasswordData({
                      current_password: '',
                      new_password: '',
                      confirm_password: '',
                    });
                  }}
                  disabled={isChangingPassword}
                  className="flex-1 px-4 py-2 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isChangingPassword}
                  className="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isChangingPassword ? 'Changing...' : 'Change Password'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}