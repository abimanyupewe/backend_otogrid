"""
Re-export models for Django discovery.
"""
from apps.authentication.data.models import User, UserRole

__all__ = ['User', 'UserRole']
