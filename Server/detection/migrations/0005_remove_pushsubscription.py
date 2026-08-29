from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('detection', '0004_uploadalert_datecreated_editable'),
    ]

    operations = [
        migrations.DeleteModel(
            name='PushSubscription',
        ),
    ]
