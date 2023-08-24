# Generated by Django 4.2.4 on 2023-08-21 05:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0002_passwordreset_user_password_reset_token_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Follower',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pending_request', models.BooleanField(default=False, verbose_name='Follow request')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='Follow from...')),
                ('followed_user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='followed', to=settings.AUTH_USER_MODEL, verbose_name='Following')),
                ('followers', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='follow', to=settings.AUTH_USER_MODEL, verbose_name='followers')),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='follower',
            constraint=models.UniqueConstraint(fields=('followed_user', 'followers'), name='unique_followers'),
        ),
    ]
