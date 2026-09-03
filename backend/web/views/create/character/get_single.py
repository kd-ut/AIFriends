from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from web.models.character import Character, Voice


class GetSingleCharacterView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            character_id = request.query_params.get('character_id')
            character = Character.objects.get(id=character_id, author__user=request.user)
            voices = [
                {'id': voice.id, 'name': voice.name}
                for voice in Voice.objects.order_by('id')
            ]
            return Response({
                'result': 'success',
                'character': {
                    'id': character.id,
                    'name': character.name,
                    'profile': character.profile,
                    'photo': character.photo.url,
                    'background_image': character.background_image.url,
                    'voice_id': character.voice_id,
                },
                'voices': voices,
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })
