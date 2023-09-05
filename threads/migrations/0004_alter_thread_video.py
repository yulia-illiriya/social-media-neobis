# Generated by Django 4.2.4 on 2023-08-30 13:54

import cloudinary_storage.storage
import cloudinary_storage.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('threads', '0003_alter_photo_photo_alter_thread_video'),
    ]

    operations = [
        migrations.AlterField(
            model_name='thread',
            name='video',
            field=models.FileField(blank=True, null=True, storage=cloudinary_storage.storage.VideoMediaCloudinaryStorage(), upload_to='', validators=[cloudinary_storage.validators.validate_video], verbose_name='Видео'),
        ),
    ]