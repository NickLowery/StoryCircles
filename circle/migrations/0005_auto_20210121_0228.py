# Generated by Django 3.1.4 on 2021-01-21 02:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('circle', '0004_auto_20210121_0227'),
    ]

    operations = [
        migrations.AlterField(
            model_name='story',
            name='finish_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='story',
            name='start_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
