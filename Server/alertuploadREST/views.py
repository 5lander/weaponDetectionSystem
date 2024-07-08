from alertuploadREST.serializers import UploadAlertSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view 
from django.http import JsonResponse

##prueba para nueva rama 
@api_view(['POST'])
def postAlert(request):
    serializer = UploadAlertSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()

    else:
        return JsonResponse({'error':'Unable to process data!'},status=400)

    return Response(request.META.get('HTTP_AUTHORIZATION'))
