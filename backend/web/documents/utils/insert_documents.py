from pathlib import Path

import lancedb
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import LanceDB
from langchain_text_splitters import RecursiveCharacterTextSplitter

from web.documents.utils.custom_embeddings import CustomEmbeddings


DOCUMENTS_DIR = Path(__file__).resolve().parent.parent


def insert_documents():
    source_file = DOCUMENTS_DIR / 'data.txt'
    if not source_file.exists():
        raise FileNotFoundError(f'知识库源文件不存在：{source_file}')

    documents = TextLoader(str(source_file), encoding='utf-8').load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    texts = text_splitter.split_documents(documents)
    print(f'已切分成 {len(texts)} 个片段。')

    embeddings = CustomEmbeddings()
    database = lancedb.connect(str(DOCUMENTS_DIR / 'lancedb_storage'))
    vector_db = LanceDB.from_documents(
        documents=texts,
        embedding=embeddings,
        connection=database,
        table_name='my_knowledge_base',
        mode='overwrite',
    )
    print(f'已插入 {vector_db._table.count_rows()} 行数据。')
