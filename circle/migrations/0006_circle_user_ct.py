# Generated by Django 3.1.4 on 2021-01-22 04:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('circle', '0005_auto_20210121_0228'),
    ]

    operations = [
        migrations.AddField(
            model_name='circle',
            name='user_ct',
            field=models.IntegerField(default=0),
        ),
    ]