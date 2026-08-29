import os
from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langchain_openai import ChatOpenAI
from langgraph.constants import END, START
from langgraph.graph import StateGraph, add_messages


class MemoryGraph:
    @staticmethod
    def create_app():
        llm = ChatOpenAI(
            model='deepseek-v3.2',
            api_key=os.getenv('API_KEY'),
            base_url=os.getenv('API_BASE'),
        )

        class AgentState(TypedDict):
            messages: Annotated[Sequence[BaseMessage], add_messages]

        def model_call(state: AgentState) -> AgentState:
            response = llm.invoke(state['messages'])
            return {'messages': [response]}

        graph = StateGraph(AgentState)
        graph.add_node('agent', model_call)
        graph.add_edge(START, 'agent')
        graph.add_edge('agent', END)
        return graph.compile()
