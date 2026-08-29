from django.utils.timezone import now
from langchain_core.messages import HumanMessage, SystemMessage

from web.models.friend import Message, SystemPrompt
from web.views.friend.message.memory.graph import MemoryGraph


def create_system_message():
    prompt = ''.join(
        item.prompt
        for item in SystemPrompt.objects.filter(title='记忆').order_by('order_number')
    )
    return SystemMessage(prompt)


def create_human_message(friend):
    prompt = f'【原始记忆】\n{friend.memory}\n【最近对话】\n'
    messages = list(Message.objects.filter(friend=friend).order_by('-id')[:10])
    messages.reverse()
    for message in messages:
        prompt += f'user: {message.user_message}\n'
        prompt += f'ai: {message.output}\n'
    return HumanMessage(prompt)


def update_memory(friend):
    app = MemoryGraph.create_app()
    result = app.invoke({
        'messages': [create_system_message(), create_human_message(friend)],
    })
    friend.memory = result['messages'][-1].content[:5000]
    friend.update_time = now()
    friend.save(update_fields=['memory', 'update_time'])
