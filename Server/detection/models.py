import uuid
from django.db import models
from django.utils import timezone

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

from webdev.storage_backends import PublicMediaStorage

# Changes uploaded file name
def scrambleUploadedFilename(instance, filename):
    """
    Scramble / uglify the filename of the uploaded file, but keep the files extension (e.g., .jpg or .png)
    :param instance:
    :param filename:
    :return:
    """
    extension = filename.split(".")[-1]
    return "{}.{}".format(uuid.uuid4(), extension)

# Data model
class UploadAlert(models.Model):
    image = models.ImageField("Uploaded image", upload_to=scrambleUploadedFilename,storage=PublicMediaStorage())
    userID = models.ForeignKey(Token, on_delete=models.CASCADE)
    alertReceiver = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    # Confianza de la deteccion que origino la alerta (0.0 - 1.0). Es opcional
    # para no romper las alertas antiguas, que se guardaron sin este dato.
    confidence = models.FloatField("Confianza de la deteccion", null=True, blank=True)
    # Fecha del hecho. Antes era auto_now_add=True, que fijaba la hora del INSERT
    # y DESCARTABA cualquier valor enviado por el cliente (Django lo impone y DRF
    # lo marca de solo lectura). Eso impedia registrar una deteccion con la hora
    # real en que ocurrio, por ejemplo al procesar una grabacion previa.
    # Con default=timezone.now el comportamiento normal no cambia (si el cliente
    # no manda nada, se usa la hora actual), pero ahora SI se puede enviar la
    # hora real del suceso.
    dateCreated = models.DateTimeField("Fecha de la deteccion", default=timezone.now)

# Generate and save a token each time a user is saved in a database
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)