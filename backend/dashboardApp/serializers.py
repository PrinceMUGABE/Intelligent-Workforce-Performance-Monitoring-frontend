# dashboardApp/serializers.py

from rest_framework import serializers
from datetime import datetime


class ChartMetadataSerializer(serializers.Serializer):
    """Metadata for charts with description and keys"""
    title = serializers.CharField()
    description = serializers.CharField()
    key_insights = serializers.ListField(child=serializers.CharField())
    data_source = serializers.CharField()
    last_updated = serializers.DateTimeField()


class ChartDataPointSerializer(serializers.Serializer):
    """Base serializer for chart data points"""
    label = serializers.CharField()
    value = serializers.FloatField()
    color = serializers.CharField(required=False)
    trend = serializers.FloatField(required=False)
    additional_data = serializers.DictField(required=False)


class QuickStatSerializer(serializers.Serializer):
    """Enhanced quick stat cards with metadata"""
    id = serializers.CharField()
    title = serializers.CharField()
    value = serializers.CharField()
    previous_value = serializers.CharField(required=False)
    change = serializers.FloatField()
    change_type = serializers.ChoiceField(choices=['increase', 'decrease', 'neutral'])
    icon = serializers.CharField()
    color = serializers.CharField()
    description = serializers.CharField()
    trend_data = ChartDataPointSerializer(many=True, required=False)
    target = serializers.CharField(required=False)
    progress = serializers.FloatField(required=False)


class ActivityItemSerializer(serializers.Serializer):
    """Enhanced activity items"""
    id = serializers.IntegerField()
    user = serializers.CharField()
    user_avatar = serializers.CharField(required=False)
    action = serializers.CharField()
    timestamp = serializers.DateTimeField()
    time_ago = serializers.CharField()
    type = serializers.CharField()
    status = serializers.ChoiceField(choices=['success', 'warning', 'error', 'info'])
    metadata = serializers.DictField(required=False)


class TaskItemSerializer(serializers.Serializer):
    """Enhanced task items"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField(required=False)
    assigned_to = serializers.CharField()
    assigned_to_id = serializers.IntegerField()
    department = serializers.CharField()
    status = serializers.CharField()
    priority = serializers.CharField()
    progress = serializers.FloatField()
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    time_remaining = serializers.CharField()
    is_overdue = serializers.BooleanField()
    tags = serializers.ListField(child=serializers.CharField(), required=False)


class DepartmentSummarySerializer(serializers.Serializer):
    """Enhanced department summary"""
    id = serializers.IntegerField()
    name = serializers.CharField()
    metrics = serializers.DictField()
    employee_count = serializers.IntegerField()
    active_employees = serializers.IntegerField()
    task_completion_rate = serializers.FloatField()
    performance_score = serializers.FloatField()
    trend = serializers.FloatField()
    top_performers = serializers.ListField(child=serializers.DictField(), required=False)


class PerformanceMetricSerializer(serializers.Serializer):
    """Performance metrics with comparisons"""
    current = serializers.FloatField()
    target = serializers.FloatField()
    previous = serializers.FloatField()
    change = serializers.FloatField()
    percentile = serializers.FloatField(required=False)
    rank = serializers.IntegerField(required=False)


class AlertSerializer(serializers.Serializer):
    """Enhanced alerts with actions"""
    id = serializers.IntegerField()
    type = serializers.ChoiceField(choices=['info', 'warning', 'error', 'success'])
    title = serializers.CharField()
    message = serializers.CharField()
    timestamp = serializers.DateTimeField()
    time_ago = serializers.CharField()
    priority = serializers.ChoiceField(choices=['high', 'medium', 'low'])
    actionable = serializers.BooleanField()
    action_url = serializers.CharField(required=False)
    dismissed = serializers.BooleanField(default=False)


# ==================== CHART CONFIGURATIONS ====================

class ChartDefinition:
    """Define chart configurations with descriptions"""
    
    @staticmethod
    def get_productivity_trend_chart():
        return {
            'title': 'Productivity Trend Analysis',
            'description': 'Tracks team productivity over time, measuring task completion rates and efficiency metrics.',
            'key_insights': [
                'Above 80% indicates high performance',
                'Compare week-over-week trends',
                'Identify peak productivity periods'
            ],
            'data_source': 'Task assignments and completions',
            'type': 'area',
            'x_axis': 'Time Period',
            'y_axis': 'Productivity %'
        }
    
    @staticmethod
    def get_task_distribution_chart():
        return {
            'title': 'Task Status Distribution',
            'description': 'Overview of all tasks grouped by their current status for better workload management.',
            'key_insights': [
                'Monitor pending vs completed tasks',
                'Identify bottlenecks in active tasks',
                'Track overdue tasks requiring attention'
            ],
            'data_source': 'Task assignments',
            'type': 'pie',
            'sections': ['Pending', 'Active', 'Completed', 'Overdue']
        }
    
    @staticmethod
    def get_department_performance_chart():
        return {
            'title': 'Department Performance Comparison',
            'description': 'Compare performance metrics across departments to identify top performers and areas needing improvement.',
            'key_insights': [
                'Department with highest completion rate',
                'Departments below average performance',
                'Resource allocation opportunities'
            ],
            'data_source': 'Department analytics',
            'type': 'bar',
            'x_axis': 'Departments',
            'y_axis': 'Performance Score'
        }
    
    @staticmethod
    def get_team_ranking_chart():
        return {
            'title': 'Team Performance Rankings',
            'description': 'Individual team member performance scores to track and recognize top contributors.',
            'key_insights': [
                'Top 3 performers this month',
                'Members needing support (<60%)',
                'Performance distribution across team'
            ],
            'data_source': 'Individual performance metrics',
            'type': 'horizontal-bar',
            'x_axis': 'Performance Score',
            'y_axis': 'Team Members'
        }


# ==================== ROLE-BASED DASHBOARD SERIALIZERS ====================

class BaseDashboardSerializer(serializers.Serializer):
    """Base serializer with common fields"""
    generated_at = serializers.DateTimeField()
    user_role = serializers.CharField()
    user_name = serializers.CharField()
    greeting = serializers.CharField()
    date_range = serializers.CharField()
    
    # Common sections
    alerts = AlertSerializer(many=True)
    recent_activities = ActivityItemSerializer(many=True)
    
    # Metadata
    dashboard_version = serializers.CharField(default='2.0')


class AdminDashboardSerializer(BaseDashboardSerializer):
    """Comprehensive admin dashboard with system-wide analytics"""
    
    # Welcome section
    welcome_stats = serializers.DictField()
    
    # Quick stats with trends
    quick_stats = QuickStatSerializer(many=True)
    
    # Charts with metadata
    charts = serializers.DictField()
    
    # Productivity trend with metadata
    productivity_trend = serializers.DictField()
    productivity_trend_data = ChartDataPointSerializer(many=True)
    productivity_chart_metadata = serializers.SerializerMethodField()
    
    # Department distribution
    department_distribution = serializers.DictField()
    department_distribution_data = ChartDataPointSerializer(many=True)
    department_chart_metadata = serializers.SerializerMethodField()
    
    # Task status distribution
    task_status_distribution = serializers.DictField()
    task_status_data = ChartDataPointSerializer(many=True)
    task_chart_metadata = serializers.SerializerMethodField()
    
    # Performance comparison
    performance_comparison = serializers.DictField()
    performance_comparison_data = ChartDataPointSerializer(many=True)
    performance_chart_metadata = serializers.SerializerMethodField()
    
    # Department summaries
    department_summaries = DepartmentSummarySerializer(many=True)
    
    # Top performers
    top_performers = serializers.ListField()
    top_performers_metadata = serializers.DictField()
    
    # System health
    system_health = serializers.DictField()
    system_metrics = serializers.DictField()
    
    # Upcoming tasks
    upcoming_tasks = TaskItemSerializer(many=True)
    upcoming_tasks_metadata = serializers.DictField()
    
    # Insights and recommendations
    insights = serializers.ListField()
    recommendations = serializers.ListField()
    
    def get_productivity_chart_metadata(self, obj):
        return ChartDefinition.get_productivity_trend_chart()
    
    def get_department_chart_metadata(self, obj):
        return ChartDefinition.get_department_performance_chart()
    
    def get_task_chart_metadata(self, obj):
        return ChartDefinition.get_task_distribution_chart()
    
    def get_performance_chart_metadata(self, obj):
        return {
            'title': 'Performance by Role',
            'description': 'Compare performance metrics across different user roles to identify trends and gaps.',
            'key_insights': [
                'Role with highest efficiency',
                'Performance gaps between roles',
                'Training needs identification'
            ],
            'data_source': 'Role-based performance analytics',
            'type': 'grouped-bar',
            'x_axis': 'Time Period',
            'y_axis': 'Performance %'
        }


class ManagerDashboardSerializer(BaseDashboardSerializer):
    """Team-focused dashboard for managers"""
    
    # Team overview
    team_overview = serializers.DictField()
    quick_stats = QuickStatSerializer(many=True)
    
    # Team productivity
    team_productivity_trend = serializers.DictField()
    team_productivity_data = ChartDataPointSerializer(many=True)
    team_productivity_metadata = serializers.SerializerMethodField()
    
    # Team performance rankings
    team_rankings = serializers.DictField()
    team_rankings_data = serializers.ListField()
    team_rankings_metadata = serializers.SerializerMethodField()
    
    # Task completion trend
    task_completion_trend = serializers.DictField()
    task_completion_data = ChartDataPointSerializer(many=True)
    task_completion_metadata = serializers.SerializerMethodField()
    
    # Department summary
    department_summary = DepartmentSummarySerializer()
    
    # Team insights
    team_insights = serializers.ListField()
    team_challenges = serializers.ListField()
    team_recommendations = serializers.ListField()
    
    # Upcoming tasks
    upcoming_tasks = TaskItemSerializer(many=True)
    
    # Team members on leave
    team_availability = serializers.ListField()
    
    def get_team_productivity_metadata(self, obj):
        return {
            'title': 'Team Productivity Trend',
            'description': 'Track your team\'s productivity over time with detailed completion metrics.',
            'key_insights': [
                'Compare with department average',
                'Identify productivity patterns',
                'Monitor team workload balance'
            ],
            'data_source': 'Team task assignments',
            'type': 'line',
            'x_axis': 'Time Period',
            'y_axis': 'Productivity %'
        }
    
    def get_team_rankings_metadata(self, obj):
        return ChartDefinition.get_team_ranking_chart()
    
    def get_task_completion_metadata(self, obj):
        return {
            'title': 'Task Completion Analysis',
            'description': 'Daily task completion rates to monitor team efficiency and workload.',
            'key_insights': [
                'Peak completion days',
                'Completion rate trends',
                'Resource allocation needs'
            ],
            'data_source': 'Completed tasks',
            'type': 'bar',
            'x_axis': 'Date',
            'y_axis': 'Tasks Completed'
        }


class EmployeeDashboardSerializer(BaseDashboardSerializer):
    """Personal dashboard for employees"""
    
    # Personal welcome
    personal_welcome = serializers.DictField()
    quick_stats = QuickStatSerializer(many=True)
    
    # Performance overview
    performance_overview = serializers.DictField()
    performance_metrics = PerformanceMetricSerializer()
    
    # Personal performance trend
    my_performance_trend = serializers.DictField()
    my_performance_data = ChartDataPointSerializer(many=True)
    my_performance_metadata = serializers.SerializerMethodField()
    
    # Task breakdown
    my_task_breakdown = serializers.DictField()
    my_task_data = ChartDataPointSerializer(many=True)
    my_task_metadata = serializers.SerializerMethodField()
    
    # Active tasks
    active_tasks = TaskItemSerializer(many=True)
    upcoming_tasks = TaskItemSerializer(many=True)
    completed_tasks = serializers.ListField()
    
    # Personal insights
    personal_insights = serializers.ListField()
    achievements = serializers.ListField()
    recommendations = serializers.ListField()
    
    # Ranking
    my_ranking = serializers.DictField()
    
    # Daily schedule
    today_schedule = serializers.ListField()
    
    def get_my_performance_metadata(self, obj):
        return {
            'title': 'My Performance Trend',
            'description': 'Track your personal performance over time and see your growth trajectory.',
            'key_insights': [
                'Compare with personal best',
                'Identify improvement areas',
                'Track consistency over time'
            ],
            'data_source': 'Your task completions',
            'type': 'area',
            'x_axis': 'Time Period',
            'y_axis': 'Performance %'
        }
    
    def get_my_task_metadata(self, obj):
        return {
            'title': 'My Task Distribution',
            'description': 'Visual breakdown of your tasks by status to manage workload effectively.',
            'key_insights': [
                'Balance of pending vs completed',
                'Active tasks requiring focus',
                'Progress towards goals'
            ],
            'data_source': 'Your task assignments',
            'type': 'pie',
            'sections': ['Pending', 'Active', 'Completed', 'Missed']
        }


class AnalystDashboardSerializer(BaseDashboardSerializer):
    """Data-focused dashboard for analysts"""
    
    # Data overview
    data_overview = serializers.DictField()
    quick_stats = QuickStatSerializer(many=True)
    
    # Advanced analytics
    overall_trends = serializers.DictField()
    overall_trends_data = ChartDataPointSerializer(many=True)
    overall_trends_metadata = serializers.SerializerMethodField()
    
    # Department comparison
    department_comparison = serializers.DictField()
    department_comparison_data = ChartDataPointSerializer(many=True)
    department_comparison_metadata = serializers.SerializerMethodField()
    
    # Performance distribution
    performance_distribution = serializers.DictField()
    performance_distribution_data = ChartDataPointSerializer(many=True)
    performance_distribution_metadata = serializers.SerializerMethodField()
    
    # Efficiency metrics
    efficiency_metrics = serializers.DictField()
    efficiency_data = ChartDataPointSerializer(many=True)
    efficiency_metadata = serializers.SerializerMethodField()
    
    # Department summaries
    department_summaries = DepartmentSummarySerializer(many=True)
    
    # Statistical analysis
    statistical_summary = serializers.DictField()
    correlations = serializers.ListField()
    predictions = serializers.ListField()
    
    # Insights
    data_insights = serializers.ListField()
    trends_analysis = serializers.ListField()
    recommendations = serializers.ListField()
    
    def get_overall_trends_metadata(self, obj):
        return {
            'title': 'Organizational Performance Trends',
            'description': 'High-level view of performance metrics across the entire organization.',
            'key_insights': [
                'Overall productivity trends',
                'Seasonal patterns',
                'Growth indicators'
            ],
            'data_source': 'Aggregated performance data',
            'type': 'multi-line',
            'x_axis': 'Time Period',
            'y_axis': 'Various Metrics'
        }
    
    def get_department_comparison_metadata(self, obj):
        return ChartDefinition.get_department_performance_chart()
    
    def get_performance_distribution_metadata(self, obj):
        return {
            'title': 'Performance Distribution Analysis',
            'description': 'Statistical distribution of performance scores across all employees.',
            'key_insights': [
                'Performance quartiles',
                'Outliers identification',
                'Normal distribution analysis'
            ],
            'data_source': 'Individual performance scores',
            'type': 'histogram',
            'x_axis': 'Performance Score Range',
            'y_axis': 'Number of Employees'
        }
    
    def get_efficiency_metadata(self, obj):
        return {
            'title': 'Efficiency Metrics',
            'description': 'Key efficiency indicators including time-to-complete and resource utilization.',
            'key_insights': [
                'Average completion time',
                'Resource efficiency rate',
                'Bottleneck identification'
            ],
            'data_source': 'Task timing data',
            'type': 'gauge',
            'metrics': ['Time Efficiency', 'Resource Utilization', 'Quality Score']
        }