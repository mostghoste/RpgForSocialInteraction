# Generated by Django 5.1.4 on 2025-03-11 21:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='last_seen',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
