# Generated by Django 2.0.1 on 2018-02-03 17:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('exchange_orderbook', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='basecurrencies',
            options={'verbose_name': 'Base Currency', 'verbose_name_plural': 'Base Currencies'},
        ),
        migrations.AlterModelOptions(
            name='markets',
            options={'verbose_name': 'Market', 'verbose_name_plural': 'Markets'},
        ),
    ]