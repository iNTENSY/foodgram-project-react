from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsRetrieveAuthenticatedOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if view.action == 'retrieve' or view.action == 'me':
            return request.user.is_authenticated
        return request.method in SAFE_METHODS
