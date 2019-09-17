# Generated by Django 2.2.4 on 2019-09-14 18:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('language', '0082_media_community'),
        ('users', '0007_auto_20190905_0211'),
    ]

    operations = [
        migrations.CreateModel(
            name='Administrator',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('community', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='language.Community')),
                ('language', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to='language.Language')),
                ('user', models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]