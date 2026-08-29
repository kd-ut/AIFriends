import os

from langchain_core.embeddings import Embeddings
from openai import OpenAI


class CustomEmbeddings(Embeddings):
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('API_KEY'),
            base_url=os.getenv('API_BASE'),
        )

    def embed_documents(self, texts):
        all_embeddings = []
        for index in range(0, len(texts), 10):
            batch = [text for text in texts[index:index + 10] if text.strip()]
            if not batch:
                continue
            response = self.client.embeddings.create(
                model='text-embedding-v4',
                input=batch,
                dimensions=1024,
            )
            all_embeddings.extend(item.embedding for item in response.data)
        return all_embeddings

    def embed_query(self, text):
        return self.embed_documents([text])[0]
