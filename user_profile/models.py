from django.db import models
from user_profile.managers import UserManager
from django.contrib.auth.models import PermissionsMixin
from django.contrib.auth.base_user import AbstractBaseUser
from django.utils.translation import gettext_lazy as _ 
from config import settings


class User(AbstractBaseUser, PermissionsMixin):
    
    """Модель, которая отвечает за базового юзера"""
    
    username = models.CharField(_('username'), max_length=255, unique=True)
    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(_('phone number'), max_length=30, null=True, blank=True)
    is_active = models.BooleanField(_('active'), default=True)
    is_staff = models.BooleanField(_('staff'), default=False)
    created_at = models.DateTimeField(_('is active'), auto_now_add=True)
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)    

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        unique_together = ('username', 'email', 'phone')
        
        
class UserProfile(models.Model):
    
    """
    Профиль пользователя (создается автоматически при создании юзера). 
    Из полей автоматически заполяется только юзернейм.
    Основным ключом является поле user
    """
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE
    )
    username = models.CharField(_('Username'))
    name = models.CharField("Name", max_length=100)
    surname = models.CharField("Surname", max_length=100)
    photo = models.ImageField(upload_to='users/%Y/%m/%d/', blank=True, null=True)
    bio = models.CharField(_('Bio'), max_length=500, null=True, blank=True)
    is_private = models.BooleanField(_('Private'), default=False, db_index=True)
    number_of_followers = models.PositiveIntegerField(_("Number_of_followers"), default=0)
    number_of_following = models.PositiveBigIntegerField(_("Following"), default=0)

    def __str__(self):
        return f"{self.username}"

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")


class PasswordReset(models.Model):
    
    """Модель используется только для сброса пароля"""
    
    email = models.CharField(max_length=255)
    code = models.SmallIntegerField(unique=True)
    
    
class Follower(models.Model):
    
    """
    Промежуточная модель, которая позволяет подписываться. 
    Поле request необходимо для подписки на приватные профили.
    В положении False оно значит, что реквест не принят.
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Who follow", related_name="followed", default=None, null=True, blank=True)
    follows = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="To follow", related_name="follow", default=None, null=True, blank=True)
    pending_request = models.BooleanField("Follow request", default=True) #если юзер не приватный, то реквест как будто сразу принят
    created_at = models.DateTimeField("Follow from...", auto_now_add=True, db_index=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user','follows'],  name="unique_followers")
        ]

        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} follows {self.follows}"
    
    

