
from user_profile.models import Follower, UserProfile


def get_number_of_followers(user):
    following_count = Follower.objects.filter(user=user, pending_request=True).count()
    followers_count = Follower.objects.filter(follows=user, pending_request=True).count()
    return following_count, followers_count

