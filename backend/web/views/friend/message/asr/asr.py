import asyncio
import json
import os
import uuid

import websockets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


DEFAULT_DASHSCOPE_WSS_URL = 'wss://dashscope.aliyuncs.com/api-ws/v1/inference/'


def get_wss_url():
    configured = os.getenv('WSS_URL')
    if configured:
        return configured
    if 'dashscope.aliyuncs.com' in os.getenv('API_BASE', ''):
        return DEFAULT_DASHSCOPE_WSS_URL
    return None


class ASRView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        audio = request.FILES.get('audio')
        if not audio:
            return Response({'result': '音频不存在'}, status=400)
        if audio.size > 10 * 1024 * 1024:
            return Response({'result': '音频文件过大'}, status=413)
        if not get_wss_url():
            return Response({'result': '语音服务尚未配置'}, status=503)

        try:
            text = asyncio.run(self.run_asr_tasks(audio.read()))
            return Response({'result': 'success', 'text': text})
        except Exception:
            return Response({'result': '语音识别失败，请稍后重试'}, status=502)

    async def asr_sender(self, pcm_data, websocket, task_id):
        for index in range(0, len(pcm_data), 3200):
            await websocket.send(pcm_data[index:index + 3200])
            await asyncio.sleep(0.01)
        await websocket.send(json.dumps({
            'header': {
                'action': 'finish-task',
                'task_id': task_id,
                'streaming': 'duplex',
            },
            'payload': {'input': {}},
        }))

    async def asr_receiver(self, websocket):
        text = ''
        async for message in websocket:
            data = json.loads(message)
            event = data['header']['event']
            if event == 'result-generated':
                transcription = data['payload']['output'].get('transcription')
                if transcription and transcription.get('sentence_end'):
                    text += transcription.get('text', '')
            elif event == 'task-failed':
                raise RuntimeError(data['header'].get('error_message', '语音识别失败'))
            elif event == 'task-finished':
                break
        return text

    async def run_asr_tasks(self, pcm_data):
        task_id = uuid.uuid4().hex
        headers = {'Authorization': f"Bearer {os.getenv('API_KEY')}"}
        async with websockets.connect(get_wss_url(), additional_headers=headers) as websocket:
            await websocket.send(json.dumps({
                'header': {
                    'streaming': 'duplex',
                    'task_id': task_id,
                    'action': 'run-task',
                },
                'payload': {
                    'model': 'gummy-realtime-v1',
                    'parameters': {
                        'sample_rate': 16000,
                        'format': 'pcm',
                        'transcription_enabled': True,
                    },
                    'input': {},
                    'task': 'asr',
                    'task_group': 'audio',
                    'function': 'recognition',
                },
            }))
            async for message in websocket:
                data = json.loads(message)
                if data['header']['event'] == 'task-started':
                    break
                if data['header']['event'] == 'task-failed':
                    raise RuntimeError(data['header'].get('error_message', '语音识别启动失败'))
            _, text = await asyncio.gather(
                self.asr_sender(pcm_data, websocket, task_id),
                self.asr_receiver(websocket),
            )
            return text
