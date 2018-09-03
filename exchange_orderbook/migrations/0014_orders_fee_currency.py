# Generated by Django 2.1.1 on 2018-09-03 02:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('exchange_core', '0003_auto_20180901_1752'),
        ('exchange_orderbook', '0013_auto_20180901_2107'),
    ]

    operations = [
        migrations.AddField(
            model_name='orders',
            name='fee_currency',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='exchange_core.Currencies'),
        ),
    ]