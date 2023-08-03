from django.dispatch import receiver
from django.db.models.signals import post_save

from user.models import UserProfile
from django.contrib.auth import get_user_model

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