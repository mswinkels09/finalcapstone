# Generated by Django 3.1.4 on 2020-12-09 22:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finalcapstoneapi', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='notes',
            field=models.CharField(max_length=255, null=True),
        ),
    ]