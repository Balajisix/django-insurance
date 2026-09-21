from rest_framework.permissions import BasePermission

from .models import UserRole


class IsCustomer(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            == UserRole.CUSTOMER
        )


class IsClaimsOfficer(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            == UserRole.CLAIMS_OFFICER
        )


class IsManager(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            == UserRole.MANAGER
        )


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role
            == UserRole.ADMIN
        )


class IsClaimsStaff(BasePermission):
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