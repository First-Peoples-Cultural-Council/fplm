# Generated by Django 2.2.3 on 2019-07-12 07:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('language', '0020_auto_20190712_0715'),
    ]

    operations = [
        migrations.RenameField(
            model_name='languagelink',
            old_name='website',
            new_name='url',
        ),
    ]