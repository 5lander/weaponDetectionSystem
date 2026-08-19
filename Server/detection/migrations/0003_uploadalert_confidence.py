from django.db import migrations, models


class Migration(migrations.Migration):
    """Anade el nivel de confianza de la deteccion a UploadAlert.

    El campo es opcional (null=True) para no romper las alertas creadas antes
    de este cambio, que se guardaron sin ese dato.
    """

    dependencies = [
        ('detection', '0002_pushsubscription'),
    ]

    operations = [
        migrations.AddField(
            model_name='uploadalert',
            name='confidence',
            field=models.FloatField(
                blank=True, null=True,
                verbose_name='Confianza de la deteccion',
            ),
        ),
    ]
