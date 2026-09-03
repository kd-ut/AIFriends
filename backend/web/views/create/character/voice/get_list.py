from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from web.models.character import Voice


class GetVoiceList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        default_voice, _ = Voice.objects.get_or_create(
            voice_id='longanyang',
            defaults={'name': '默认音色'},
        )
        voices = [
            {'id': voice.id, 'name': voice.name}
            for voice in Voice.objects.order_by('id')
        ]
        return Response({'result': 'success', 'voices': voices})
