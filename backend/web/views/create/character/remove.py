from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from web.models.character import Character


class RemoveCharacterView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            character_id = request.data['character_id']
            Character.objects.filter(pk=character_id, author__user=request.user).delete()
            return Response({
                'result': 'success'
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })
