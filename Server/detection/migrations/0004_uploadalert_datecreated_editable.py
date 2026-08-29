"""Permite registrar una alerta con la hora REAL en que ocurrio.

`dateCreated` era `auto_now_add=True`: Django fijaba la hora del INSERT e
ignoraba cualquier valor enviado por el cliente (DRF ademas lo exponia como
campo de solo lectura). Con `default=timezone.now` el comportamiento habitual no
cambia -si no se envia nada se usa la hora actual-, pero ahora se puede subir
una deteccion fechada en el momento en que sucedio, por ejemplo al procesar una
grabacion posterior al hecho.

Las filas existentes conservan su valor: la migracion solo altera la definicion
del campo, no los datos.
"""
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('detection', '0003_uploadalert_confidence'),
    ]

    operations = [
        migrations.AlterField(
            model_name='uploadalert',
            name='dateCreated',
            field=models.DateTimeField(
                default=django.utils.timezone.now,
                verbose_name='Fecha de la deteccion',
            ),
        ),
    ]
