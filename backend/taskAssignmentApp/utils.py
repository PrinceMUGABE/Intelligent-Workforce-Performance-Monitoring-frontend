# taskAssignmentApp/utils.py

from .models import TaskAssignment

def get_assignment_status_values():
    """Extract status values from TaskAssignment model"""
    return [status[0] for status in TaskAssignment.STATUS_CHOICES]

def get_assignment_status_dict():
    """Get status choices as a dictionary"""
    return dict(TaskAssignment.STATUS_CHOICES)

def get_priority_values():
    """Extract priority values from TaskAssignment model"""
    return [priority[0] for priority in TaskAssignment.PRIORITY_CHOICES]

def get_priority_dict():
    """Get priority choices as a dictionary"""
    return dict(TaskAssignment.PRIORITY_CHOICES)