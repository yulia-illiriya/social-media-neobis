# Generated by Django 4.2.4 on 2023-10-10 05:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('threads', '0010_alter_video_thread'),
    ]

    operations = [
        migrations.AlterField(
            model_name='photo',
            name='photo',
            field=models.ImageField(upload_to=''),
        ),
    ]
