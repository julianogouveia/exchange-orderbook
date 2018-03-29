# Generated by Django 2.0.1 on 2018-03-29 15:07

from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exchange_orderbook', '0007_basecurrencies_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='markets',
            name='max_price',
            field=models.DecimalField(decimal_places=8, default=Decimal('1000000.00'), max_digits=20),
        ),
    ]
