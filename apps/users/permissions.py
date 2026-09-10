from rest_framework.permissions import BasePermission

from .models import UserRole


class IsCustomer(BasePermission):
    """
    Allows only customer users.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            == UserRole.CUSTOMER
        )


class IsClaimsOfficer(BasePermission):
    """
    Allows only claims officers.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            == UserRole.CLAIMS_OFFICER
        )


class IsManager(BasePermission):
    """
    Allows only managers.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            == UserRole.MANAGER
        )


class IsAdmin(BasePermission):
    """
    Allows only application administrators.
    """

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            == UserRole.ADMIN
        )


class IsClaimsStaff(BasePermission):
    """
    Allows claims officers, managers and admins.
    """

    allowed_roles = {
        UserRole.CLAIMS_OFFICER,
        UserRole.MANAGER,
        UserRole.ADMIN,
    }

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            in self.allowed_roles
        )