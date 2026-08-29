import json
import logging

from django.http import StreamingHttpResponse
from langchain_core.messages import AIMessage, BaseMessageChunk, HumanMessage, SystemMessage
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import BaseRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from web.models.friend import Friend, Message, SystemPrompt
from web.views.friend.message.chat.graph import ChatGraph
from web.views.friend.message.memory.update import update_memory


logger = logging.getLogger(__name__)


class SSERenderer(BaseRenderer):
    media_type = 'text/event-stream'
    format = 'txt'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


def add_system_prompt(state, friend):
    prompt = ''.join(
        item.prompt
        for item in SystemPrompt.objects.filter(title='回复').order_by('order_number')
    )
    prompt += f'\n【角色性格】\n{friend.character.profile}\n'
    prompt += f'【长期记忆】\n{friend.memory}\n'
    return {'messages': [SystemMessage(prompt)] + state['messages']}


def add_recent_messages(state, friend):
    recent = list(Message.objects.filter(friend=friend).order_by('-id')[:10])
    recent.reverse()
    history = []
    for message in recent:
        history.append(HumanMessage(message.user_message))
        history.append(AIMessage(message.output))
    return {'messages': state['messages'][:1] + history + state['messages'][-1:]}


class MessageChatView(APIView):
    permission_classes = [IsAuthenticated]
    renderer_classes = [SSERenderer]

    def post(self, request):
        friend_id = request.data.get('friend_id')
        message = str(request.data.get('message', '')).strip()
        if not message:
            return Response({'result': '消息不能为空'}, status=400)

        friend = Friend.objects.filter(pk=friend_id, me__user=request.user).first()
        if friend is None:
            return Response({'result': '好友不存在'}, status=404)

        app = ChatGraph.create_app()
        inputs = add_recent_messages(
            add_system_prompt({'messages': [HumanMessage(message)]}, friend),
            friend,
        )

        def event_stream():
            full_output = ''
            full_usage = {}
            for chunk, metadata in app.stream(inputs, stream_mode='messages'):
                if not isinstance(chunk, BaseMessageChunk):
                    continue
                if chunk.content:
                    full_output += chunk.content
                    payload = json.dumps({'content': chunk.content}, ensure_ascii=False)
                    yield f'data: {payload}\n\n'
                if getattr(chunk, 'usage_metadata', None):
                    full_usage = chunk.usage_metadata

            yield 'data: [DONE]\n\n'
            Message.objects.create(
                friend=friend,
                user_message=message[:500],
                input=json.dumps(
                    [item.model_dump() for item in inputs['messages']],
                    ensure_ascii=False,
                )[:10000],
                output=full_output[:500],
                input_tokens=full_usage.get('input_tokens', 0),
                output_tokens=full_usage.get('output_tokens', 0),
                total_tokens=full_usage.get('total_tokens', 0),
            )

            # 5.2 的行为：每产生一条回复就更新一次长期记忆。
            try:
                update_memory(friend)
            except Exception:
                logger.exception('更新好友长期记忆失败，当前聊天记录已正常保存。')

        response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response
