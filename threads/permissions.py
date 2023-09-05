from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Пермишен, который позволяет только владельцам ретвитов удалять
    """
    def has_object_permission(self, request, view, obj):
        # Разрешено GET, HEAD, и OPTIONS запросы всем
        if request.method in permissions.SAFE_METHODS:
            return True

        # Разрешено редактирование и удаление только владельцам объекта
        return obj.who_added == request.user