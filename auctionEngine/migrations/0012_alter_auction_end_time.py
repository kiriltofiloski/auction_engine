# Generated by Django 5.1.7 on 2025-04-03 09:50

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auctionEngine', '0011_alter_auction_end_time'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auction',
            name='end_time',
            field=models.DateTimeField(default=datetime.datetime(2025, 4, 4, 9, 50, 25, 957416, tzinfo=datetime.timezone.utc)),
        ),
    ]
