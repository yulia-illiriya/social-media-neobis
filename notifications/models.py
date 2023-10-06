from django.db import models
from user_profile.models import User


class Activity(models.Model):
    EVENT_TYPES = (
        ('subscription', 'following'),
        ('subscription_request', 'pending_request'),
        ('post_like', 'Лайк поста'),
        ('post_comment', 'Комментарий к посту'),
        ('post_repost', 'Репост'),
        ('post_quote', 'Цитата'),
    )
    event_type = models.CharField("Тип активности", max_length=20, choices=EVENT_TYPES)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.CharField("Сообщение", max_length=255)
    created_at = models.DateTimeField("Событие произошло в", auto_now_add=True)

    def __str__(self):
        return f'{self.message}'
