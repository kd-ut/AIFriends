from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response

from web.models.character import Character
from web.models.user import UserProfile


class GetListCharacterView(APIView):
    def get(self, request):
        try:
            items_count = int(request.query_params.get('items_count'))
            user_id = int(request.query_params.get('user_id'))
            user = User.objects.get(id=user_id)
            user_profile = UserProfile.objects.get(user=user)
            characters_raw = Character.objects.filter(
                author=user_profile
            ).order_by('-id')[items_count: items_count + 20]
            characters = []
            for character in characters_raw:
                author = character.author
                characters.append({
                    'id': character.id,
                    'name': character.name,
                    'profile': character.profile,
                    'photo': character.photo.url,
                    'background_image': character.background_image.url,
                    'author': {
                        'user_id': author.user_id,
                        'username': author.user.username,
                        'photo': author.photo.url,
                    }
                })
            return Response({
                'result': 'success',
                'user_profile': {
                    'user_id': user.id,
                    'username': user.username,
                    'profile': user_profile.profile,
                    'photo': user_profile.photo.url,
                },
                'characters': characters,
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })
