# Generated by Django 3.1.4 on 2020-12-11 19:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finalcapstoneapi', '0004_auto_20201211_1948'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='returned',
            field=models.BooleanField(blank=True, null=True),
        ),
    ]
