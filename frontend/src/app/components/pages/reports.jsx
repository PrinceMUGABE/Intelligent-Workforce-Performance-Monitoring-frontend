/* eslint-disable react-hooks/exhaustive-deps */
/* eslint-disable no-unused-vars */
import { useState, useEffect } from 'react';
import { useAuth } from '../../context/auth-context';
import { 
  FileText, 
  Download, 
  Calendar, 
  Filter, 
  FileSpreadsheet, 
  FileType,
  Users,
  Building2,
  CheckSquare,
  ClipboardList,
  CalendarOff,
  Activity,
  TrendingUp,
  Building,
  ChevronDown,
  ChevronUp,
  Loader2,
  X,
  Search,
  Settings
} from 'lucide-react';
import { toast } from 'sonner';
import { Toaster } from 'sonner';
import * as XLSX from 'xlsx';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

// Base URL for report endpoints
const REPORT_BASE_URL = 'http://127.0.0.1:8000/report';
const API_BASE_URL = 'http://127.0.0.1:8000';

export default function Reports() {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [availableReports, setAvailableReports] = useState([]);
  const [reportData, setReportData] = useState(null);
  const [showFilters, setShowFilters] = useState(false);
  const [showColumnPicker, setShowColumnPicker] = useState(false);
  
  // Filter states
  const [reportType, setReportType] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [departmentId, setDepartmentId] = useState('');
  const [userId, setUserId] = useState('');
  const [status, setStatus] = useState('');
  const [priority, setPriority] = useState('');
  
  // Data for dropdowns
  const [departments, setDepartments] = useState([]);
  const [users, setUsers] = useState([]);
  
  // Table filtering
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState('');
  const [sortDirection, setSortDirection] = useState('asc');
  
  // Column selection for export
  const [selectedColumns, setSelectedColumns] = useState([]);
  const [availableColumns, setAvailableColumns] = useState([]);

  // Helper function to get auth headers
  const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token');
    return {
      'Authorization': token ? `Bearer ${token}` : '',
      'Content-Type': 'application/json',
    };
  };

  // Generic fetch function with authentication
  const authenticatedFetch = async (url, options = {}) => {
    const headers = getAuthHeaders();
    
    const response = await fetch(url, {
      ...options,
      headers: {
        ...headers,
        ...options.headers,
      },
    });

    if (!response.ok) {
      if (response.status === 401) {
        // Token expired or invalid
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        throw new Error('Session expired. Please login again.');
      }
      
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.message || `Request failed with status ${response.status}`);
    }

    return response.json();
  };

  // Fetch available reports on mount
  useEffect(() => {
    fetchAvailableReports();
    fetchDepartments();
    if (user?.role !== 'employee') {
      fetchUsers();
    }
  }, [user]);

  // Update available columns and select all by default when report data changes
  useEffect(() => {
    if (reportData) {
      const tableData = getTableData(reportData);
      setAvailableColumns(tableData.headers);
      setSelectedColumns(tableData.headers); // Select all by default
    }
  }, [reportData]);

  const fetchAvailableReports = async () => {
    try {
      const data = await authenticatedFetch(`${REPORT_BASE_URL}/available/`);
      setAvailableReports(data.available_reports || []);
    } catch (error) {
      console.error('Error fetching available reports:', error);
      toast.error(error.message || 'Failed to load available reports');
    }
  };

  const fetchDepartments = async () => {
    try {
      const data = await authenticatedFetch(`${API_BASE_URL}/departments/all/`);
      setDepartments(data.departments || []);
    } catch (error) {
      console.error('Error fetching departments:', error);
      toast.error(error.message || 'Failed to load departments');
    }
  };

  const fetchUsers = async () => {
    try {
      const data = await authenticatedFetch(`${API_BASE_URL}/users/`);
      setUsers(data.users || []);
    } catch (error) {
      console.error('Error fetching users:', error);
      toast.error(error.message || 'Failed to load users');
    }
  };

  const getReportEndpoint = (type) => {
    const endpoints = {
      'user_report': 'users/',
      'department_report': 'departments/',
      'task_report': 'tasks/',
      'task_assignment_report': 'assignments/',
      'dayoff_report': 'dayoff/',
      'activity_report': 'activities/',
      'performance_report': 'performance/',
      'organization_report': 'organization/',
    };
    return endpoints[type] || '';
  };

  const getReportTitle = (type) => {
    const titles = {
      'user_report': 'User Report',
      'department_report': 'Department Report',
      'task_report': 'Task Report',
      'task_assignment_report': 'Task Assignment Report',
      'dayoff_report': 'Day-Off Request Report',
      'activity_report': 'Activity Report',
      'performance_report': 'Performance Report',
      'organization_report': 'Organization Report',
    };
    return titles[type] || 'Report';
  };

  const handleGenerateReport = async () => {
    if (!reportType) {
      toast.error('Please select a report type');
      return;
    }

    setLoading(true);
    setReportData(null);

    try {
      const endpoint = getReportEndpoint(reportType);
      const filters = {};

      if (startDate) filters.start_date = startDate;
      if (endDate) filters.end_date = endDate;
      if (departmentId) filters.department_id = departmentId;
      if (userId) filters.user_id = userId;
      if (status) filters.status = status;
      if (priority) filters.priority = priority;

      const data = await authenticatedFetch(`${REPORT_BASE_URL}/${endpoint}`, {
        method: 'POST',
        body: JSON.stringify(filters),
      });
      
      setReportData(data);
      toast.success('Report generated successfully!');
    } catch (error) {
      console.error('Error generating report:', error);
      toast.error(error.message || 'Failed to generate report');
    } finally {
      setLoading(false);
    }
  };

  const toggleColumnSelection = (column) => {
    setSelectedColumns(prev => {
      if (prev.includes(column)) {
        return prev.filter(c => c !== column);
      } else {
        return [...prev, column];
      }
    });
  };

  const selectAllColumns = () => {
    setSelectedColumns(availableColumns);
  };

  const deselectAllColumns = () => {
    setSelectedColumns([]);
  };

  const getFilteredTableData = (tableData) => {
    if (selectedColumns.length === 0) {
      return tableData; // Return all if none selected
    }

    const columnIndices = selectedColumns.map(col => tableData.headers.indexOf(col));
    
    return {
      headers: selectedColumns,
      rows: tableData.rows.map(row => 
        columnIndices.map(index => row[index])
      )
    };
  };

  const handleExportPDF = () => {
    if (!reportData) {
      toast.error('No report data to export');
      return;
    }

    if (selectedColumns.length === 0) {
      toast.error('Please select at least one column to export');
      return;
    }

    try {
      const doc = new jsPDF();
      const pageWidth = doc.internal.pageSize.width;
      const pageHeight = doc.internal.pageSize.height;
      
      // Header
      doc.setFillColor(79, 70, 229); // Indigo
      doc.rect(0, 0, pageWidth, 40, 'F');
      
      doc.setTextColor(255, 255, 255);
      doc.setFontSize(20);
      doc.setFont('helvetica', 'bold');
      doc.text('CodePulse Africa Ltd', pageWidth / 2, 15, { align: 'center' });
      
      doc.setFontSize(12);
      doc.setFont('helvetica', 'normal');
      doc.text('Intelligent Workforce Performance Monitoring', pageWidth / 2, 25, { align: 'center' });
      
      doc.setFontSize(10);
      doc.text('Confidential Report', pageWidth / 2, 35, { align: 'center' });
      
      // Report Title
      doc.setTextColor(0, 0, 0);
      doc.setFontSize(16);
      doc.setFont('helvetica', 'bold');
      doc.text(getReportTitle(reportType), 14, 55);
      
      // Report Info
      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.text(`Generated on: ${new Date(reportData.summary.generated_at).toLocaleString()}`, 14, 65);
      doc.text(`Generated by: ${reportData.summary.generated_by}`, 14, 72);
      doc.text(`Report Type: ${reportData.summary.report_type}`, 14, 79);
      doc.text(`Total Records: ${reportData.summary.total_count}`, 14, 86);
      
      // Summary Section
      doc.setFontSize(12);
      doc.setFont('helvetica', 'bold');
      doc.text('Key Metrics', 14, 100);
      
      const summaryData = extractSummaryData(reportData);
      const summaryTable = summaryData.map(item => [item.label, item.value]);
      
      autoTable(doc, {
        startY: 105,
        head: [['Metric', 'Value']],
        body: summaryTable,
        theme: 'grid',
        headStyles: { fillColor: [79, 70, 229], textColor: 255 },
        styles: { fontSize: 9 },
        margin: { left: 14, right: 14 }
      });
      
      // Data Table with selected columns only
      const tableData = getTableData(reportData);
      const filteredData = getFilteredTableData(tableData);
      
      if (filteredData.headers.length > 0 && filteredData.rows.length > 0) {
        doc.addPage();
        
        doc.setFontSize(12);
        doc.setFont('helvetica', 'bold');
        doc.text('Detailed Data', 14, 20);
        
        autoTable(doc, {
          startY: 25,
          head: [filteredData.headers],
          body: filteredData.rows,
          theme: 'striped',
          headStyles: { fillColor: [79, 70, 229], textColor: 255 },
          styles: { fontSize: 8 },
          margin: { left: 14, right: 14 },
          columnStyles: filteredData.headers.reduce((acc, _, index) => {
            acc[index] = { cellWidth: 'auto' };
            return acc;
          }, {})
        });
      }
      
      // Footer
      const totalPages = doc.internal.getNumberOfPages();
      for (let i = 1; i <= totalPages; i++) {
        doc.setPage(i);
        doc.setFontSize(8);
        doc.setTextColor(100);
        doc.text(
          `Confidential Information - CodePulse Africa Ltd`,
          pageWidth / 2,
          pageHeight - 10,
          { align: 'center' }
        );
        doc.text(
          `Page ${i} of ${totalPages}`,
          pageWidth - 20,
          pageHeight - 10,
          { align: 'right' }
        );
      }
      
      doc.save(`${getReportTitle(reportType)}_${new Date().toISOString().split('T')[0]}.pdf`);
      toast.success('PDF exported successfully!');
    } catch (error) {
      console.error('PDF export error:', error);
      toast.error(`Failed to export PDF: ${error.message}`);
    }
  };

  const handleExportExcel = () => {
    if (!reportData) {
      toast.error('No report data to export');
      return;
    }

    if (selectedColumns.length === 0) {
      toast.error('Please select at least one column to export');
      return;
    }

    try {
      const wb = XLSX.utils.book_new();
      
      // Summary Sheet
      const summaryData = extractSummaryData(reportData);
      const summaryWS = XLSX.utils.json_to_sheet([
        { A: 'CodePulse Africa Ltd' },
        { A: 'Intelligent Workforce Performance Monitoring' },
        { A: '' },
        { A: 'Report Information' },
        { A: 'Report Type', B: reportData.summary.report_type },
        { A: 'Generated On', B: new Date(reportData.summary.generated_at).toLocaleString() },
        { A: 'Generated By', B: reportData.summary.generated_by },
        { A: 'Total Records', B: reportData.summary.total_count },
        { A: '' },
        { A: 'Key Metrics' },
        ...summaryData.map(item => ({ A: item.label, B: item.value }))
      ], { skipHeader: true });
      
      XLSX.utils.book_append_sheet(wb, summaryWS, 'Summary');
      
      // Data Sheet with selected columns only
      const tableData = getTableData(reportData);
      const filteredData = getFilteredTableData(tableData);
      
      if (filteredData.headers.length > 0 && filteredData.rows.length > 0) {
        const dataForExcel = filteredData.rows.map(row => {
          const obj = {};
          filteredData.headers.forEach((header, index) => {
            obj[header] = row[index];
          });
          return obj;
        });
        
        const dataWS = XLSX.utils.json_to_sheet(dataForExcel);
        XLSX.utils.book_append_sheet(wb, dataWS, 'Data');
      }
      
      XLSX.writeFile(wb, `${getReportTitle(reportType)}_${new Date().toISOString().split('T')[0]}.xlsx`);
      toast.success('Excel exported successfully!');
    } catch (error) {
      console.error('Excel export error:', error);
      toast.error('Failed to export Excel');
    }
  };

  const handleExportCSV = () => {
    if (!reportData) {
      toast.error('No report data to export');
      return;
    }

    if (selectedColumns.length === 0) {
      toast.error('Please select at least one column to export');
      return;
    }

    try {
      const tableData = getTableData(reportData);
      const filteredData = getFilteredTableData(tableData);
      
      if (!filteredData.headers || !filteredData.rows) {
        toast.error('No data to export');
        return;
      }

      let csv = filteredData.headers.join(',') + '\n';
      filteredData.rows.forEach(row => {
        csv += row.map(cell => `"${cell}"`).join(',') + '\n';
      });

      const blob = new Blob([csv], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${getReportTitle(reportType)}_${new Date().toISOString().split('T')[0]}.csv`;
      a.click();
      window.URL.revokeObjectURL(url);
      
      toast.success('CSV exported successfully!');
    } catch (error) {
      console.error('CSV export error:', error);
      toast.error('Failed to export CSV');
    }
  };

  const extractSummaryData = (data) => {
    const summary = [];
    
    if (data.statistics) {
      Object.entries(data.statistics).forEach(([key, value]) => {
        if (typeof value === 'object' && !Array.isArray(value)) {
          Object.entries(value).forEach(([subKey, subValue]) => {
            summary.push({
              label: `${formatLabel(key)} - ${formatLabel(subKey)}`,
              value: subValue
            });
          });
        } else if (!Array.isArray(value)) {
          summary.push({
            label: formatLabel(key),
            value: value
          });
        }
      });
    }
    
    return summary;
  };

  const formatLabel = (str) => {
    return str
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const getTableData = (data) => {
    // Determine which data key to use
    const dataKeys = ['users', 'departments', 'tasks', 'assignments', 'day_off_requests', 'activities', 'performance_data'];
    let dataKey = dataKeys.find(key => data[key]);
    
    if (!dataKey || !data[dataKey]) {
      return { headers: [], rows: [] };
    }

    // Handle performance_data specially - it can be an object or array
    let items;
    if (dataKey === 'performance_data') {
      // If it's already an array (org-wide performance), use it directly
      // If it's an object (single user performance), wrap it in an array
      items = Array.isArray(data[dataKey]) ? data[dataKey] : [data[dataKey]];
    } else {
      items = Array.isArray(data[dataKey]) ? data[dataKey] : [data[dataKey]];
    }
    
    if (items.length === 0) {
      return { headers: [], rows: [] };
    }

    // Get headers from first item
    const firstItem = items[0];
    const headers = Object.keys(firstItem).filter(key => 
      typeof firstItem[key] !== 'object' || firstItem[key] === null
    );

    // Get rows
    const rows = items.map(item => 
      headers.map(header => {
        const value = item[header];
        if (value === null || value === undefined) return 'N/A';
        if (typeof value === 'boolean') return value ? 'Yes' : 'No';
        if (typeof value === 'number') return value.toString();
        return value.toString();
      })
    );

    return {
      headers: headers.map(formatLabel),
      rows
    };
  };

  const getFilteredData = () => {
    if (!reportData) return { headers: [], rows: [] };
    
    const tableData = getTableData(reportData);
    
    if (!searchTerm && !sortField) {
      return tableData;
    }

    let filteredRows = [...tableData.rows];

    // Apply search filter
    if (searchTerm) {
      filteredRows = filteredRows.filter(row =>
        row.some(cell => 
          cell.toString().toLowerCase().includes(searchTerm.toLowerCase())
        )
      );
    }

    // Apply sorting
    if (sortField) {
      const headerIndex = tableData.headers.indexOf(sortField);
      if (headerIndex !== -1) {
        filteredRows.sort((a, b) => {
          const aVal = a[headerIndex];
          const bVal = b[headerIndex];
          
          if (sortDirection === 'asc') {
            return aVal > bVal ? 1 : -1;
          } else {
            return aVal < bVal ? 1 : -1;
          }
        });
      }
    }

    return {
      headers: tableData.headers,
      rows: filteredRows
    };
  };

  const handleSort = (header) => {
    if (sortField === header) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(header);
      setSortDirection('asc');
    }
  };

  const resetFilters = () => {
    setStartDate('');
    setEndDate('');
    setDepartmentId('');
    setUserId('');
    setStatus('');
    setPriority('');
    setSearchTerm('');
    setSortField('');
    setSortDirection('asc');
  };

  const getReportIcon = (type) => {
    const icons = {
      'user_report': Users,
      'department_report': Building2,
      'task_report': CheckSquare,
      'task_assignment_report': ClipboardList,
      'dayoff_report': CalendarOff,
      'activity_report': Activity,
      'performance_report': TrendingUp,
      'organization_report': Building,
    };
    return icons[type] || FileText;
  };

  // Check if user is authenticated
  if (!localStorage.getItem('access_token')) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-slate-900 mb-4">Authentication Required</h2>
          <p className="text-slate-600 mb-6">Please log in to access reports.</p>
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

  return (
    <div className="space-y-6">
      <Toaster position="top-center" richColors />

      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-slate-900">Reports</h1>
        <p className="text-slate-600 mt-1">
          Generate comprehensive reports for workforce performance monitoring
        </p>
      </div>

      {/* Report Configuration */}
      <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-slate-900">Report Configuration</h2>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 px-4 py-2 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
          >
            <Filter className="w-5 h-5" />
            {showFilters ? 'Hide Filters' : 'Show Filters'}
          </button>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Report Type *
            </label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
            >
              <option value="">Select report type...</option>
              {availableReports.map((report) => (
                <option key={report} value={report}>
                  {getReportTitle(report)}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Start Date
              </label>
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                End Date
              </label>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
              />
            </div>
          </div>
        </div>

        {/* Advanced Filters */}
        {showFilters && (
          <div className="mt-6 pt-6 border-t border-slate-200">
            <h3 className="text-sm font-semibold text-slate-900 mb-4">Advanced Filters</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {user?.role !== 'employee' && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Department
                    </label>
                    <select
                      value={departmentId}
                      onChange={(e) => setDepartmentId(e.target.value)}
                      className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                    >
                      <option value="">All Departments</option>
                      {departments.map((dept) => (
                        <option key={dept.id} value={dept.id}>
                          {dept.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      User
                    </label>
                    <select
                      value={userId}
                      onChange={(e) => setUserId(e.target.value)}
                      className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                    >
                      <option value="">All Users</option>
                      {users.map((u) => (
                        <option key={u.id} value={u.id}>
                          {u.full_name}
                        </option>
                      ))}
                    </select>
                  </div>
                </>
              )}

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Status
                </label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                >
                  <option value="">All Statuses</option>
                  <option value="pending">Pending</option>
                  <option value="approved">Approved</option>
                  <option value="active">Active</option>
                  <option value="completed">Completed</option>
                  <option value="scheduled">Scheduled</option>
                  <option value="missed">Missed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>

              {(reportType === 'task_assignment_report') && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Priority
                  </label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                  >
                    <option value="">All Priorities</option>
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
              )}
            </div>

            <div className="mt-4 flex gap-3">
              <button
                onClick={resetFilters}
                className="px-4 py-2 text-slate-600 hover:bg-slate-50 rounded-lg transition-colors flex items-center gap-2"
              >
                <X className="w-4 h-4" />
                Reset Filters
              </button>
            </div>
          </div>
        )}

        <div className="mt-6 flex gap-3">
          <button
            onClick={handleGenerateReport}
            disabled={loading || !reportType}
            className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center gap-2"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <FileText className="w-5 h-5" />
                Generate Report
              </>
            )}
          </button>
        </div>
      </div>

      {/* Report Results */}
      {reportData && (
        <>
          {/* Summary Section */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-xl font-bold text-slate-900">
                  {reportData.summary.report_type}
                </h2>
                <p className="text-sm text-slate-600 mt-1">
                  Generated on {new Date(reportData.summary.generated_at).toLocaleString()} by {reportData.summary.generated_by}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowColumnPicker(!showColumnPicker)}
                  className="p-2 hover:bg-indigo-50 rounded-lg transition-colors"
                  title="Select Columns"
                >
                  <Settings className="w-5 h-5 text-indigo-600" />
                </button>
                <button
                  onClick={handleExportPDF}
                  className="p-2 hover:bg-red-50 rounded-lg transition-colors"
                  title="Export PDF"
                >
                  <FileType className="w-5 h-5 text-red-600" />
                </button>
                <button
                  onClick={handleExportExcel}
                  className="p-2 hover:bg-emerald-50 rounded-lg transition-colors"
                  title="Export Excel"
                >
                  <FileSpreadsheet className="w-5 h-5 text-emerald-600" />
                </button>
                <button
                  onClick={handleExportCSV}
                  className="p-2 hover:bg-sky-50 rounded-lg transition-colors"
                  title="Export CSV"
                >
                  <Download className="w-5 h-5 text-sky-600" />
                </button>
              </div>
            </div>

            {/* Column Picker */}
            {showColumnPicker && (
              <div className="mb-6 p-4 bg-slate-50 rounded-lg border border-slate-200">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-slate-900">Select Columns to Export</h3>
                  <div className="flex gap-2">
                    <button
                      onClick={selectAllColumns}
                      className="text-xs px-3 py-1 text-indigo-600 hover:bg-indigo-50 rounded transition-colors"
                    >
                      Select All
                    </button>
                    <button
                      onClick={deselectAllColumns}
                      className="text-xs px-3 py-1 text-slate-600 hover:bg-slate-100 rounded transition-colors"
                    >
                      Deselect All
                    </button>
                  </div>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                  {availableColumns.map((column) => (
                    <label
                      key={column}
                      className="flex items-center gap-2 p-2 hover:bg-white rounded cursor-pointer transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={selectedColumns.includes(column)}
                        onChange={() => toggleColumnSelection(column)}
                        className="w-4 h-4 text-indigo-600 rounded focus:ring-2 focus:ring-indigo-500"
                      />
                      <span className="text-sm text-slate-700">{column}</span>
                    </label>
                  ))}
                </div>
                <p className="text-xs text-slate-500 mt-3">
                  {selectedColumns.length} of {availableColumns.length} columns selected
                </p>
              </div>
            )}

            {/* Key Metrics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard
                label="Total Records"
                value={reportData.summary.total_count}
                icon={FileText}
                color="indigo"
              />
              {extractSummaryData(reportData).slice(0, 7).map((metric, index) => (
                <MetricCard
                  key={index}
                  label={metric.label}
                  value={metric.value}
                  color="slate"
                />
              ))}
            </div>
          </div>

          {/* Data Table */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-slate-900">
                Detailed Data ({getFilteredData().rows.length} records)
              </h2>
              <div className="flex items-center gap-3">
                <div className="relative">
                  <Search className="w-5 h-5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="Search data..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                  />
                </div>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200">
                    {getFilteredData().headers.map((header, index) => (
                      <th
                        key={index}
                        onClick={() => handleSort(header)}
                        className="px-4 py-3 text-left text-sm font-semibold text-slate-700 cursor-pointer hover:bg-slate-100 transition-colors"
                      >
                        <div className="flex items-center gap-2">
                          {header}
                          {sortField === header && (
                            sortDirection === 'asc' ? 
                              <ChevronUp className="w-4 h-4" /> : 
                              <ChevronDown className="w-4 h-4" />
                          )}
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  {getFilteredData().rows.length > 0 ? (
                    getFilteredData().rows.map((row, rowIndex) => (
                      <tr key={rowIndex} className="hover:bg-slate-50 transition-colors">
                        {row.map((cell, cellIndex) => (
                          <td key={cellIndex} className="px-4 py-3 text-sm text-slate-600">
                            {cell}
                          </td>
                        ))}
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td 
                        colSpan={getFilteredData().headers.length} 
                        className="px-4 py-8 text-center text-slate-500"
                      >
                        No data found matching your search criteria
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Empty State */}
      {!reportData && !loading && (
        <div className="bg-white p-12 rounded-xl shadow-sm border border-slate-200 text-center">
          <FileText className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-2">No Report Generated</h3>
          <p className="text-slate-600 mb-6">
            Select a report type and click "Generate Report" to view data
          </p>
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value, icon: Icon, color = 'slate' }) {
  const colorClasses = {
    indigo: 'bg-indigo-100 text-indigo-600',
    slate: 'bg-slate-100 text-slate-600',
    emerald: 'bg-emerald-100 text-emerald-600',
    red: 'bg-red-100 text-red-600',
  };

  return (
    <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
      <div className="flex items-center gap-3">
        {Icon && (
          <div className={`w-10 h-10 ${colorClasses[color]} rounded-lg flex items-center justify-center`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
        <div>
          <p className="text-xs text-slate-600 mb-1">{label}</p>
          <p className="text-lg font-bold text-slate-900">
            {typeof value === 'number' ? value.toLocaleString() : value}
          </p>
        </div>
      </div>
    </div>
  );
}