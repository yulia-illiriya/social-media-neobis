# Generated by Django 4.2.4 on 2023-10-06 05:22

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Activity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(choices=[('subscription', 'following'), ('subscription_request', 'pending_request'), ('post_like', 'Лайк поста'), ('post_comment', 'Комментарий к посту'), ('post_repost', 'Репост'), ('post_quote', 'Цитата')], max_length=20, verbose_name='Тип активности')),
                ('message', models.CharField(max_length=255, verbose_name='Сообщение')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Событие произошло в')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
