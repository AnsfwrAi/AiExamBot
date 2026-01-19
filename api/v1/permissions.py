from rest_framework.permissions import BasePermission

class TokenPermission(BasePermission):
    def has_permission(self, request, view):
        auth = request.META.get('HTTP_AUTHORIZATION')
        if not auth:
            raise Exception("die")
        if auth.split(' ')[1] != 'hjsdgUYGshdgu7fugyasuygukybasdargyutfvcuzgbasdsdtgx67':
            raise Exception("die")
        return True
