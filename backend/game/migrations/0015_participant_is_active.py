# Generated by Django 5.1.7 on 2025-03-24 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0014_alter_character_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
