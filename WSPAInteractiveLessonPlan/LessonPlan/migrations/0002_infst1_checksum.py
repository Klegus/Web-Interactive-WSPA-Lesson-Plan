# Generated by Django 4.2.7 on 2023-11-11 11:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('LessonPlan', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='infst1',
            name='checksum',
            field=models.CharField(default='', max_length=64),
        ),
    ]
