# Generated by Django 4.2.5 on 2023-11-08 21:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quizzes', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='quiz',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]
