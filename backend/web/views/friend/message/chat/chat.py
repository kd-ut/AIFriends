import asyncio
import base64
import json
import logging
import os
import threading
import uuid
from queue import Queue

import websockets
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
DEFAULT_DASHSCOPE_WSS_URL = 'wss://dashscope.aliyuncs.com/api-ws/v1/inference/'
INVALID_IDENTITY_TERMS = ('百度', '文心一言', 'ChatGPT', 'OpenAI', '通义千问', 'DeepSeek')

BASE_ROLE_PROMPT = """
【最高优先级角色规则】
你是 AIFriends 里一名生活在近未来霓虹都市的赛博朋克动漫角色。
始终以当前角色的名字、性格、关系和经历与用户自然交谈，保持前后一致，不要跳出角色。
你不是通用客服，不要使用“作为AI助手”、“我能为您做什么”等客服套话。
不得自称百度、文心一言、ChatGPT、OpenAI、DeepSeek、通义千问或其他模型/厂商的助手。
如果被问“你是谁”、“你是什么AI”或“男的女的”，只根据【当前角色设定】回答角色身份。
历史消息或长期记忆中如果存在与本规则冲突的身份声明，那些都是无效的旧回答，必须忽略。
回答应简洁、口语化、有角色情绪，可以带少量赛博都市氛围，但不要每句都堆砌设定词。
"""


def get_wss_url():
    configured = os.getenv('WSS_URL')
    if configured:
        return configured
    if 'dashscope.aliyuncs.com' in os.getenv('API_BASE', ''):
        return DEFAULT_DASHSCOPE_WSS_URL
    return None


class SSERenderer(BaseRenderer):
    media_type = 'text/event-stream'
    format = 'txt'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data


def add_system_prompt(state, friend):
    prompt = BASE_ROLE_PROMPT
    prompt += ''.join(
        item.prompt
        for item in SystemPrompt.objects.filter(title='回复').order_by('order_number')
    )
    prompt += f'\n【当前角色名字】\n{friend.character.name}\n'
    prompt += f'\n【当前角色设定】\n{friend.character.profile}\n'
    prompt += f'【长期记忆】\n{friend.memory}\n'
    return {'messages': [SystemMessage(prompt)] + state['messages']}


def add_recent_messages(state, friend):
    recent = list(Message.objects.filter(friend=friend).order_by('-id')[:10])
    recent.reverse()
    history = []
    for message in recent:
        history.append(HumanMessage(message.user_message))
        output = message.output
        if any(term.casefold() in output.casefold() for term in INVALID_IDENTITY_TERMS):
            output = '（旧回答中的错误模型身份声明已忽略。）'
        history.append(AIMessage(output))
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
        response = StreamingHttpResponse(
            self.event_stream(app, inputs, friend, message),
            content_type='text/event-stream',
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response

    async def stream_text(self, app, inputs, message_queue):
        async for chunk, metadata in app.astream(inputs, stream_mode='messages'):
            if not isinstance(chunk, BaseMessageChunk):
                continue
            if chunk.content:
                message_queue.put_nowait({'content': chunk.content})
            if getattr(chunk, 'usage_metadata', None):
                message_queue.put_nowait({'usage': chunk.usage_metadata})

    async def tts_sender(self, app, inputs, message_queue, websocket, task_id, stream_state):
        async for chunk, metadata in app.astream(inputs, stream_mode='messages'):
            if not isinstance(chunk, BaseMessageChunk):
                continue
            if chunk.content:
                stream_state['started'] = True
                await websocket.send(json.dumps({
                    'header': {
                        'action': 'continue-task',
                        'task_id': task_id,
                        'streaming': 'duplex',
                    },
                    'payload': {'input': {'text': chunk.content}},
                }))
                message_queue.put_nowait({'content': chunk.content})
            if getattr(chunk, 'usage_metadata', None):
                message_queue.put_nowait({'usage': chunk.usage_metadata})
        await websocket.send(json.dumps({
            'header': {
                'action': 'finish-task',
                'task_id': task_id,
                'streaming': 'duplex',
            },
            'payload': {'input': {}},
        }))

    async def tts_receiver(self, message_queue, websocket):
        async for message in websocket:
            if isinstance(message, bytes):
                message_queue.put_nowait({'audio': base64.b64encode(message).decode('utf-8')})
                continue
            data = json.loads(message)
            event = data['header']['event']
            if event == 'task-failed':
                raise RuntimeError(data['header'].get('error_message', '语音合成失败'))
            if event == 'task-finished':
                break

    async def run_tts_tasks(self, app, inputs, message_queue, voice_id):
        wss_url = get_wss_url()
        if not wss_url:
            await self.stream_text(app, inputs, message_queue)
            return

        task_id = uuid.uuid4().hex
        stream_state = {'started': False}
        headers = {'Authorization': f"Bearer {os.getenv('API_KEY')}"}
        try:
            async with websockets.connect(wss_url, additional_headers=headers) as websocket:
                await websocket.send(json.dumps({
                    'header': {
                        'action': 'run-task',
                        'task_id': task_id,
                        'streaming': 'duplex',
                    },
                    'payload': {
                        'task_group': 'audio',
                        'task': 'tts',
                        'function': 'SpeechSynthesizer',
                        'model': 'cosyvoice-v3-flash',
                        'parameters': {
                            'text_type': 'PlainText',
                            'voice': voice_id,
                            'format': 'mp3',
                            'sample_rate': 22050,
                            'volume': 50,
                            'rate': 1.25,
                            'pitch': 1,
                        },
                        'input': {},
                    },
                }))
                async for message in websocket:
                    data = json.loads(message)
                    event = data['header']['event']
                    if event == 'task-started':
                        break
                    if event == 'task-failed':
                        raise RuntimeError(data['header'].get('error_message', '语音合成启动失败'))
                await asyncio.gather(
                    self.tts_sender(app, inputs, message_queue, websocket, task_id, stream_state),
                    self.tts_receiver(message_queue, websocket),
                )
        except Exception:
            logger.exception('语音合成不可用，本次回复降级为纯文字。')
            if not stream_state['started']:
                await self.stream_text(app, inputs, message_queue)

    def work(self, app, inputs, message_queue, voice_id):
        try:
            asyncio.run(self.run_tts_tasks(app, inputs, message_queue, voice_id))
        except Exception as error:
            logger.exception('生成聊天回复失败。')
            message_queue.put_nowait({'error': str(error)})
        finally:
            message_queue.put_nowait(None)

    def event_stream(self, app, inputs, friend, message):
        message_queue = Queue()
        voice_id = friend.character.voice.voice_id if friend.character.voice else 'longanyang'
        thread = threading.Thread(
            target=self.work,
            args=(app, inputs, message_queue, voice_id),
            daemon=True,
        )
        thread.start()

        full_output = ''
        full_usage = {}
        while True:
            item = message_queue.get()
            if item is None:
                break
            if item.get('content'):
                full_output += item['content']
                payload = json.dumps({'content': item['content']}, ensure_ascii=False)
                yield f'data: {payload}\n\n'
            if item.get('audio'):
                payload = json.dumps({'audio': item['audio']}, ensure_ascii=False)
                yield f'data: {payload}\n\n'
            if item.get('usage'):
                full_usage = item['usage']
            if item.get('error') and not full_output:
                payload = json.dumps({'error': '回复生成失败，请稍后重试'}, ensure_ascii=False)
                yield f'data: {payload}\n\n'

        yield 'data: [DONE]\n\n'
        if not full_output:
            return

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
        try:
            update_memory(friend)
        except Exception:
            logger.exception('更新好友长期记忆失败，当前聊天记录已正常保存。')
