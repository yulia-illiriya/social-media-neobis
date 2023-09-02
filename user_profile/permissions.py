from rest_framework import permissions
from user_profile.models import User, UserProfile, Follower

class CanAccessPrivateThreads(permissions.BasePermission):
    message = "Профиль приватный. Для просмотра тредов подпишитесь."

    def has_permission(self, request, view):
        user = request.user
        username = view.kwargs['username']
        requested_user_profile = UserProfile.objects.get(username=username)
        if requested_user_profile.is_private:            
            is_following = Follower.objects.filter(user=user, follows=requested_user_profile.user, pending_request=True).exists()
            if not is_following:
                    return False

        return True