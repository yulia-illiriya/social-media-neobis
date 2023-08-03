from django.contrib.auth.base_user import BaseUserManager

class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username=None, email=None, phone=None, password=None, **extra_fields):
        
        """
        Create and save a User with the given email and password.
        If user do not post username, we use email as username
        """
        if not email:
                raise ValueError('Введите почту')
        email = self.normalize_email(email)

        if not username:
                username = email

        user = self.model(
                email=email,
                username=username,
                **extra_fields
            )
        
        # проверяем является ли пользователь суперпользователем
        if extra_fields.get('is_superuser'):
            user = self.model(
                username=username,
                **extra_fields
            )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username=username, email=email, password=password, **extra_fields)

    def create_superuser(self, username, password, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(
            username=username,
            password=password,
            **extra_fields
        )