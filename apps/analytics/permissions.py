from rest_framework.permissions import BasePermission


class IsAnalyticsUser(BasePermission):

    message = (
        "You do not have permission to access insurance analytics."
    )

    ALLOWED_ROLES = {
        "CLAIMS_OFFICER",
        "MANAGER",
        "ADMIN",
    }

    def has_permission(self, request, view):

        if not request.user or not request.user.is_authenticated:
            return False

        if getattr(request.user, "is_superuser", False):
            return True

        role = getattr(
            request.user,
            "role",
            None,
        )

        return role in self.ALLOWED_ROLES