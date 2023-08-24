from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, pre_save

from user_profile.models import Follower, UserProfile
from django.contrib.auth import get_user_model
from .utils import get_number_of_followers

User = get_user_model()


profile_created = False  # Глобальная переменная для отслеживания создания профиля

@receiver(post_save, sender=User, dispatch_uid="create_profile")
def create_profile(sender, instance, created, **kwargs):
    """
    Создаём профиль пользователя при регистрации - событие происходит автоматически
    """
    global profile_created

    if created and not profile_created:
        UserProfile.objects.create(
            user=instance, #связываем профиль с одним юзером
            username=instance.username,  # автоматически также передаем юзернейм            
        )
        profile_created = True
        
        


@receiver(post_save, sender=Follower)
@receiver(post_delete, sender=Follower)
def update_followers_count(sender, instance, **kwargs):
    user_profile = instance.user.userprofile
    following_count = Follower.objects.filter(user=instance.user, pending_request=True).count() #за кем следим мы
    followers_count = Follower.objects.filter(follows=instance.user, pending_request=True).count()
    user_profile.number_of_following = following_count
    user_profile.number_of_followers = followers_count
    user_profile.save()



@receiver(pre_save, sender=Follower)
def update_followers_count_on_update(sender, instance, **kwargs):
    if instance.pk:  # Если это обновление объекта, а не создание нового
        old_instance = Follower.objects.get(pk=instance.pk)

        if old_instance.pending_request != instance.pending_request:
            # Если изменилось состояние pending_request
            new_user_profile = instance.user.userprofile
            new_following_count = Follower.objects.filter(user=instance.user, pending_request=True).count()
            new_followers_count = Follower.objects.filter(follows=instance.user, pending_request=True).count()
            new_user_profile.number_of_following = new_following_count
            new_user_profile.number_of_followers = new_followers_count
            new_user_profile.save()