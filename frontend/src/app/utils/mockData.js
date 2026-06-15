export const mockDepartments = [
  { id: 'D001', name: 'Technology', description: 'IT and Software Development', managerId: 'U002', employeeCount: 15, createdAt: '2023-01-10' },
  { id: 'D002', name: 'Marketing', description: 'Marketing and Communications', managerId: 'U003', employeeCount: 12, createdAt: '2023-01-10' },
  { id: 'D003', name: 'Sales', description: 'Sales and Business Development', managerId: 'U004', employeeCount: 18, createdAt: '2023-01-10' },
  { id: 'D004', name: 'Human Resources', description: 'HR and Administration', managerId: 'U005', employeeCount: 8, createdAt: '2023-01-10' },
  { id: 'D005', name: 'Finance', description: 'Finance and Accounting', managerId: 'U006', employeeCount: 10, createdAt: '2023-01-10' },
  { id: 'D006', name: 'Operations', description: 'Operations Management', managerId: 'U007', employeeCount: 20, createdAt: '2023-01-10' },
];

export const mockUsers = [
  { id: 'U001', name: 'Mugabo Eric', email: 'mugabo.eric@company.com', role: 'admin', department: 'Technology', departmentId: 'D001', status: 'active', joinDate: '2021-08-14' },
  { id: 'U002', name: 'Uwase Divine', email: 'uwase.divine@company.com', role: 'manager', department: 'Technology', departmentId: 'D001', status: 'active', joinDate: '2022-03-10' },
  { id: 'U003', name: 'Niyonzima Jean', email: 'niyonzima.jean@company.com', role: 'manager', department: 'Marketing', departmentId: 'D002', status: 'active', joinDate: '2022-06-10' },
  { id: 'U004', name: 'Kamikazi Alice', email: 'kamikazi.alice@company.com', role: 'manager', department: 'Sales', departmentId: 'D003', status: 'active', joinDate: '2022-05-15' },
  { id: 'U005', name: 'Habimana Patrick', email: 'habimana.patrick@company.com', role: 'manager', department: 'Human Resources', departmentId: 'D004', status: 'active', joinDate: '2022-04-20' },
  { id: 'U006', name: 'Mukashema Grace', email: 'mukashema.grace@company.com', role: 'manager', department: 'Finance', departmentId: 'D005', status: 'active', joinDate: '2022-07-12' },
  { id: 'U007', name: 'Nsengimana Claude', email: 'nsengimana.claude@company.com', role: 'manager', department: 'Operations', departmentId: 'D006', status: 'active', joinDate: '2022-08-05' },
  { id: 'U008', name: 'Umutoni Sandra', email: 'umutoni.sandra@company.com', role: 'data-analyst', department: 'Technology', departmentId: 'D001', status: 'active', joinDate: '2023-01-15' },
  { id: 'U009', name: 'Nshuti Daniel', email: 'nshuti.daniel@company.com', role: 'employee', department: 'Technology', departmentId: 'D001', status: 'active', joinDate: '2023-02-20' },
  { id: 'U010', name: 'Uwizeye Marie', email: 'uwizeye.marie@company.com', role: 'employee', department: 'Marketing', departmentId: 'D002', status: 'active', joinDate: '2023-03-22' },
  { id: 'U011', name: 'Bizimana Fred', email: 'bizimana.fred@company.com', role: 'employee', department: 'Sales', departmentId: 'D003', status: 'active', joinDate: '2023-04-10' },
  { id: 'U012', name: 'Umutoniwase Peace', email: 'umutoniwase.peace@company.com', role: 'employee', department: 'Sales', departmentId: 'D003', status: 'active', joinDate: '2023-05-18' },
  { id: 'U013', name: 'Kalisa Emmanuel', email: 'kalisa.emmanuel@company.com', role: 'employee', department: 'Finance', departmentId: 'D005', status: 'active', joinDate: '2023-06-25' },
  { id: 'U014', name: 'Iradukunda Ange', email: 'iradukunda.ange@company.com', role: 'employee', department: 'Operations', departmentId: 'D006', status: 'active', joinDate: '2023-07-30' },
  { id: 'U015', name: 'Tuyishime David', email: 'tuyishime.david@company.com', role: 'employee', department: 'Human Resources', departmentId: 'D004', status: 'active', joinDate: '2023-09-12' },
];

export const mockTasks = [
  { id: 'T001', title: 'Website Redesign Project', description: 'Complete redesign of company website with modern UI/UX', priority: 'high', status: 'in_progress', createdAt: '2025-01-05', createdBy: 'U002', dueDate: '2025-02-15', estimatedDays: 30 },
  { id: 'T002', title: 'Q1 Marketing Campaign', description: 'Plan and execute Q1 marketing campaigns across all channels', priority: 'urgent', status: 'in_progress', createdAt: '2025-01-08', createdBy: 'U003', dueDate: '2025-02-01', estimatedDays: 20 },
  { id: 'T003', title: 'Sales Target Analysis', description: 'Analyze Q4 sales performance and set Q1 targets', priority: 'high', status: 'completed', createdAt: '2025-01-02', createdBy: 'U004', dueDate: '2025-01-20', estimatedDays: 15 },
  { id: 'T004', title: 'Employee Onboarding System', description: 'Develop automated employee onboarding system', priority: 'medium', status: 'pending', createdAt: '2025-01-10', createdBy: 'U005', dueDate: '2025-03-01', estimatedDays: 45 },
  { id: 'T005', title: 'Financial Report Q4', description: 'Prepare comprehensive financial report for Q4 2024', priority: 'urgent', status: 'completed', createdAt: '2024-12-28', createdBy: 'U006', dueDate: '2025-01-15', estimatedDays: 10 },
  { id: 'T006', title: 'Mobile App Development', description: 'Develop mobile application for customer engagement', priority: 'high', status: 'in_progress', createdAt: '2025-01-03', createdBy: 'U002', dueDate: '2025-03-30', estimatedDays: 60 },
  { id: 'T007', title: 'Customer Feedback Analysis', description: 'Analyze customer feedback and prepare improvement recommendations', priority: 'medium', status: 'in_progress', createdAt: '2025-01-12', createdBy: 'U007', dueDate: '2025-02-10', estimatedDays: 25 },
  { id: 'T008', title: 'Database Optimization', description: 'Optimize database queries and improve performance', priority: 'high', status: 'pending', createdAt: '2025-01-15', createdBy: 'U002', dueDate: '2025-02-20', estimatedDays: 30 },
];

export const mockTaskAssignments = [
  { id: 'TA001', taskId: 'T001', taskTitle: 'Website Redesign Project', employeeId: 'U009', employeeName: 'Nshuti Daniel', assignedAt: '2025-01-05', assignedBy: 'U002', daysToComplete: 30, status: 'in_progress', progress: 65 },
  { id: 'TA002', taskId: 'T002', taskTitle: 'Q1 Marketing Campaign', employeeId: 'U010', employeeName: 'Uwizeye Marie', assignedAt: '2025-01-08', assignedBy: 'U003', daysToComplete: 20, status: 'in_progress', progress: 45 },
  { id: 'TA003', taskId: 'T003', taskTitle: 'Sales Target Analysis', employeeId: 'U011', employeeName: 'Bizimana Fred', assignedAt: '2025-01-02', assignedBy: 'U004', daysToComplete: 15, status: 'completed', completedAt: '2025-01-18', progress: 100 },
  { id: 'TA004', taskId: 'T003', taskTitle: 'Sales Target Analysis', employeeId: 'U012', employeeName: 'Umutoniwase Peace', assignedAt: '2025-01-02', assignedBy: 'U004', daysToComplete: 15, status: 'completed', completedAt: '2025-01-19', progress: 100 },
  { id: 'TA005', taskId: 'T005', taskTitle: 'Financial Report Q4', employeeId: 'U013', employeeName: 'Kalisa Emmanuel', assignedAt: '2024-12-28', assignedBy: 'U006', daysToComplete: 10, status: 'completed', completedAt: '2025-01-14', progress: 100 },
  { id: 'TA006', taskId: 'T006', taskTitle: 'Mobile App Development', employeeId: 'U009', employeeName: 'Nshuti Daniel', assignedAt: '2025-01-03', assignedBy: 'U002', daysToComplete: 60, status: 'in_progress', progress: 35 },
  { id: 'TA007', taskId: 'T007', taskTitle: 'Customer Feedback Analysis', employeeId: 'U014', employeeName: 'Iradukunda Ange', assignedAt: '2025-01-12', assignedBy: 'U007', daysToComplete: 25, status: 'in_progress', progress: 50 },
  { id: 'TA008', taskId: 'T001', taskTitle: 'Website Redesign Project', employeeId: 'U008', employeeName: 'Umutoni Sandra', assignedAt: '2025-01-05', assignedBy: 'U002', daysToComplete: 30, status: 'in_progress', progress: 70 },
];

// Calculate performance from task assignments
export const mockPerformanceData = mockUsers
  .filter(user => user.role === 'employee' || user.role === 'data-analyst')
  .map(user => {
    const userAssignments = mockTaskAssignments.filter(ta => ta.employeeId === user.id);
    const totalTasks = userAssignments.length;
    const completedTasks = userAssignments.filter(ta => ta.status === 'completed').length;
    const taskCompletionRate = totalTasks > 0 ? Math.round((completedTasks / totalTasks) * 100) : 0;
    const avgProgress = totalTasks > 0 ? Math.round(userAssignments.reduce((sum, ta) => sum + ta.progress, 0) / totalTasks) : 0;
    const productivityScore = avgProgress;
    const attendanceRate = 95 + Math.floor(Math.random() * 5); // Mock attendance
    
    let trend = 'stable';
    if (taskCompletionRate >= 90) trend = 'up';
    else if (taskCompletionRate < 70) trend = 'down';
    
    return {
      id: user.id,
      employeeName: user.name,
      employeeId: user.id,
      department: user.department,
      productivityScore,
      attendanceRate,
      taskCompletionRate,
      completedTasks,
      totalTasks,
      period: 'Q1 2025',
      trend
    };
  });

export const mockAuditLogs = [
  { id: '1', user: 'mugabo.eric@company.com', action: 'User Created', timestamp: '2025-01-22 10:30:00', details: 'Created user: nshuti.daniel@company.com' },
  { id: '2', user: 'niyonzima.jean@company.com', action: 'Report Generated', timestamp: '2025-01-22 11:15:00', details: 'Generated monthly performance report' },
  { id: '3', user: 'mugabo.eric@company.com', action: 'User Updated', timestamp: '2025-01-22 14:45:00', details: 'Updated role for: uwizeye.marie@company.com' },
  { id: '4', user: 'umutoni.sandra@company.com', action: 'Data Export', timestamp: '2025-01-22 16:20:00', details: 'Exported performance data (CSV)' },
  { id: '5', user: 'mugabo.eric@company.com', action: 'Task Assigned', timestamp: '2025-01-22 09:15:00', details: 'Assigned task: Website Redesign to Nshuti Daniel' },
  { id: '6', user: 'uwase.divine@company.com', action: 'Task Updated', timestamp: '2025-01-22 13:30:00', details: 'Updated task status: Mobile App Development' },
  { id: '7', user: 'habimana.patrick@company.com', action: 'Department Created', timestamp: '2025-01-15 08:00:00', details: 'Created department: Operations' },
];

export const getChartData = () => {
  return [
    { month: 'Jul', productivity: 85, attendance: 92, completion: 88 },
    { month: 'Aug', productivity: 87, attendance: 94, completion: 90 },
    { month: 'Sep', productivity: 89, attendance: 93, completion: 91 },
    { month: 'Oct', productivity: 91, attendance: 95, completion: 93 },
    { month: 'Nov', productivity: 90, attendance: 96, completion: 94 },
    { month: 'Dec', productivity: 92, attendance: 97, completion: 95 },
    { month: 'Jan', productivity: 93, attendance: 98, completion: 96 },
  ];
};

export const getDepartmentData = () => {
  return mockDepartments.map(dept => ({
    department: dept.name,
    count: dept.employeeCount,
    avgScore: 85 + Math.floor(Math.random() * 10)
  }));
};