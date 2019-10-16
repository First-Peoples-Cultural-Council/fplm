# Generated by Django 2.2.4 on 2019-10-14 17:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('language', '0088_media_creator'),
    ]

    operations = [
        migrations.AlterField(
            model_name='community',
            name='other_names',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='favourite',
            name='place',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='favourites', to='language.PlaceName'),
        ),
        migrations.AlterField(
            model_name='language',
            name='other_names',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AlterField(
            model_name='placename',
            name='language',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='places', to='language.Language'),
        ),
        migrations.AlterField(
            model_name='placename',
            name='other_names',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
    ]