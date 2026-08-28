from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from web.models.user import UserProfile


class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            username = request.data.get("username").strip()
            password = request.data.get("password").strip()
            if not username or not password:
                return Response({
                    'result': '用户名和密码不能为空'
                })
            user = authenticate(username=username, password=password)
            if user:  # 用户名密码正确
                # 兼容在 UserProfile 模型加入之前创建的已有用户。
                user_profile, _ = UserProfile.objects.get_or_create(user=user)
                refresh = RefreshToken.for_user(user)  # 生成jwt
                response = Response({
                    'result': 'success',
                    'access': str(refresh.access_token),
                    'user_id': user.id,
                    'username': user.username,
                    'photo': user_profile.photo.url,  # 必须加url！！！
                    'profile': user_profile.profile,
                })
                response.set_cookie(
                    key='refresh_token',
                    value=str(refresh),
                    httponly=True,
                    samesite='Lax',
                    secure=True,
                    max_age=86400 * 7,
                )
                return response
            return Response({
                'result': '用户名或密码错误'
            })
        except:
            return Response({
                'result': '系统异常，请稍后重试'
            })
