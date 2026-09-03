import os
from pathlib import Path
from typing import Annotated, Sequence, TypedDict

import lancedb
from django.utils.timezone import localtime, now
from langchain_community.vectorstores import LanceDB
from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.constants import END, START
from langgraph.graph import StateGraph, add_messages
from langgraph.prebuilt import ToolNode

from web.documents.utils.custom_embeddings import CustomEmbeddings


DOCUMENTS_DIR = Path(__file__).resolve().parents[4] / 'documents'


class ChatGraph:
    @staticmethod
    def create_app():
        @tool
        def get_time() -> str:
            """当需要查询精确时间时，调用此函数。返回格式为：[年-月-日 时:分:秒]"""
            return localtime(now()).strftime('%Y-%m-%d %H:%M:%S')

        @tool
        def search_knowledge_base(query: str) -> str:
            """当用户查询阿里云百炼平台的相关信息时，调用此函数。"""
            database_path = DOCUMENTS_DIR / 'lancedb_storage'
            if not database_path.exists():
                return '知识库尚未初始化，暂时无法检索相关资料。'

            database = lancedb.connect(str(database_path))
            if 'my_knowledge_base' not in database.table_names():
                return '知识库尚未初始化，暂时无法检索相关资料。'

            vector_db = LanceDB(
                connection=database,
                embedding=CustomEmbeddings(),
                table_name='my_knowledge_base',
            )
            documents = vector_db.similarity_search(query, k=3)
            context = '\n\n'.join(
                f'内容片段：{index + 1}\n{document.page_content}'
                for index, document in enumerate(documents)
            )
            return f'从知识库中找到以下相关信息：\n\n{context}\n'

        tools = [get_time, search_knowledge_base]

        # 聊天模型和阿里云语音服务使用独立配置。配置了 CHAT_API_KEY 时，
        # 使用 DeepSeek 官方接口；未配置时继续回退到原有的阿里百炼模型，
        # 避免影响语音识别、语音合成和现有本地开发环境。
        chat_api_key = os.getenv('CHAT_API_KEY')
        if chat_api_key:
            chat_api_base = os.getenv('CHAT_API_BASE', 'https://api.deepseek.com')
            chat_model = os.getenv('CHAT_MODEL', 'deepseek-v4-flash')
        else:
            chat_api_key = os.getenv('API_KEY')
            chat_api_base = os.getenv('API_BASE')
            chat_model = 'deepseek-v3.2'

        llm = ChatOpenAI(
            model=chat_model,
            api_key=chat_api_key,
            base_url=chat_api_base,
            streaming=True,
            model_kwargs={
                'stream_options': {'include_usage': True},
            },
        ).bind_tools(tools)

        class AgentState(TypedDict):
            messages: Annotated[Sequence[BaseMessage], add_messages]

        def model_call(state: AgentState) -> AgentState:
            response = llm.invoke(state['messages'])
            return {'messages': [response]}

        def should_continue(state: AgentState) -> str:
            return 'tools' if state['messages'][-1].tool_calls else 'end'

        graph = StateGraph(AgentState)
        graph.add_node('agent', model_call)
        graph.add_node('tools', ToolNode(tools))
        graph.add_edge(START, 'agent')
        graph.add_conditional_edges('agent', should_continue, {'tools': 'tools', 'end': END})
        graph.add_edge('tools', 'agent')
        return graph.compile()
