# Generated by Django 2.1 on 2018-08-31 14:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('exchange_orderbook', '0009_ohlc'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Earnings',
            new_name='Matchs',
        ),
        migrations.AlterModelOptions(
            name='orders',
            options={'verbose_name': 'Order', 'verbose_name_plural': 'Orders'},
        ),
    ]
