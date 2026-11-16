import os
import math
from operator import itemgetter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import load_prompt
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_community.retrievers.bm25 import BM25Retriever
from langchain.retrievers.ensemble import EnsembleRetriever


class Assistant:
    def __init__(self, **kwargs):
        self.dirs = kwargs.get('dirs', {})
        self.model_cfgs = kwargs.get('model')
        self.embedding_cfg = kwargs.get('embedding')

        self.set_model()
        self.embeddings = OpenAIEmbeddings(model=self.embedding_cfg['embedding_model_name'])

    def set_model(self, system_prompt_file="default.yaml", input_variables={}):
        extra_body = {}
        if self.model_cfgs.get('enable_thinking') is False:
            extra_body["chat_template_kwargs"] = {"enable_thinking": False}
        self.model = ChatOpenAI(
            model=self.model_cfgs['model_name'],
            temperature=self.model_cfgs['temperature'],
            base_url=self.model_cfgs.get('base_url'),
            api_key=self.model_cfgs.get('api_key'),
            extra_body=extra_body or None,
            )
        # Set system message on model
        prompt_path = os.path.join(self.dirs['prompt'], 'patent_qa/system', system_prompt_file)
        system_prompt = load_prompt(prompt_path)
        system_prompt = system_prompt.format(**input_variables)
        self.system_prompt = system_prompt

    def embed_documents(self, docs):
        chunk_size = 70
        num_split = math.ceil(len(docs) / chunk_size)
        self.vectorstore = FAISS.from_documents(
            documents=docs[:chunk_size],
            embedding=self.embeddings
        )
        for i in range(1, num_split):
            chunk = docs[chunk_size*i : chunk_size*(i+1)]
            if chunk:
                self.vectorstore.add_documents(chunk)

    def set_retriever(self, **kwargs):
        search_type = kwargs.get("search_type", "similarity")
        search_kwargs = kwargs.get("search_kwargs", {"k": 30})
        bm25_weights = kwargs.get("bm25_weights", 0.7)

        faiss_retriever = self.vectorstore.as_retriever(
            search_type=search_type, search_kwargs=search_kwargs
        )
        bm25_retriever = BM25Retriever.from_documents(
            self.vectorstore.docstore._dict.values()
        )
        self.retriever = EnsembleRetriever(
            retrievers = [bm25_retriever, faiss_retriever],
            weights = [bm25_weights, 1-bm25_weights]
        )

    def create_prompt(self, task, few_shot=None):
        template_f = os.path.join(self.dirs['prompt'], 'patent_qa/user', f"{task}.yaml")
        prompt = load_prompt(template_f)

        if few_shot is not None:
            example_dir = os.path.join(self.dirs['example'], task)
            examples = [a for a in os.listdir(example_dir) if '.txt' in a]
            examples.sort()

            example_prompt = "---\n#Examples\n"
            for filename in examples[:few_shot]:
                example_f = os.path.join(example_dir, filename)
                with open(example_f, 'r') as rf:
                    example_prompt += "\n\n" + rf.read()

            prompt = prompt.partial(example=example_prompt)


        return prompt

    def set_reranker(self, **kwargs):
        #rerank_model = kwargs.get('rerank_model', 'BAAI/bge-m3')
        rerank_model = kwargs.get("rerank_model", "BAAI/bge-reranker-base")
        top_n = kwargs.get('top_n', 5)

        cross_encoder = HuggingFaceCrossEncoder(model_name=rerank_model)
        compressor = CrossEncoderReranker(model=cross_encoder, top_n=top_n)
        self.reranker = ContextualCompressionRetriever(
            base_compressor=compressor, base_retriever=self.retriever
        )
