# Generated by Django 3.2.12 on 2022-03-14 21:29

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clover', '0002_auto'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='clvmodel',
            options={'verbose_name': '5. CLV Model', 'verbose_name_plural': '5. CLV Models'},
        ),
        migrations.AlterModelOptions(
            name='config',
            options={'verbose_name': '6. Configuration', 'verbose_name_plural': '6. Configurations'},
        ),
        migrations.RemoveField(
            model_name='clvmodel',
            name='config',
        ),
        migrations.RemoveField(
            model_name='config',
            name='app',
        ),
        migrations.AddField(
            model_name='account',
            name='app',
            field=models.ManyToManyField(blank=True, related_name='app_account', to='clover.ApplicationAPIKey'),
        ),
        migrations.AddField(
            model_name='account',
            name='user',
            field=models.ManyToManyField(blank=True, related_name='user_account', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='clvmodel',
            name='data_set',
            field=models.ForeignKey(default='', on_delete=django.db.models.deletion.CASCADE,
                                    related_name='data_clvmodel', to='clover.trainingdataset'),
            preserve_default=False,
        ),
    ]
