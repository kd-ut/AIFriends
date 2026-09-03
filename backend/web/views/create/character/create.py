from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from web.models.character import Character, Voice
from web.models.user import UserProfile


class CreateCharacterView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        try:
            user = request.user
            user_profile = UserProfile.objects.get(user=user)
            name = request.data.get('name').strip()
            voice_id = request.data.get('voice_id')
            profile = request.data.get('profile').strip()[:100000]
            photo = request.FILES.get('photo', None)
            background_image = request.FILES.get('background_image', None)

            if not name:
                return Response({
                    'result': '名字不能为空'
                })
            if not profile:
                return Response({
                    'result': '角色介绍不能为空'
                })
            if not photo:
                return Response({
                    'result': '头像不能为空'
                })
            if not background_image:
                return Response({
                    'result': '聊天背景不能为空'
                })

            voice = Voice.objects.filter(id=voice_id).first()
            if voice is None:
                return Response({'result': '请选择有效音色'})

            Character.objects.create(
                author=user_profile,
                name=name,
                voice=voice,
                profile=profile,
                photo=photo,
                background_image=background_image,
            )
            return Response({
                'result': 'success',
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })
