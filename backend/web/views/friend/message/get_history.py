from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from web.models.friend import Message


class GetHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            last_message_id = int(request.query_params.get('last_message_id', 0))
            friend_id = request.query_params.get('friend_id')
            queryset = Message.objects.filter(
                friend_id=friend_id,
                friend__me__user=request.user,
            )
            if last_message_id > 0:
                queryset = queryset.filter(pk__lt=last_message_id)

            messages = [
                {
                    'id': message.id,
                    'user_message': message.user_message,
                    'output': message.output,
                }
                for message in queryset.order_by('-id')[:10]
            ]
            return Response({'result': 'success', 'messages': messages})
        except (TypeError, ValueError):
            return Response({'result': '请求参数错误'}, status=400)
        except Exception:
            return Response({'result': '系统异常，请稍后重试'}, status=500)
