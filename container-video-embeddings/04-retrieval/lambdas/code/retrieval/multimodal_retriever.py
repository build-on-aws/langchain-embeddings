import json
from typing import List, Dict
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from embeddings import get_embeddings
from aurora_service import AuroraPostgres


class CustomMultimodalRetriever(BaseRetriever):
    """A retriever that contains the top k documents that contain the user query.
    query could be text or image_bytes
    """

    aurora_cluster: AuroraPostgres

    k: int
    """Number of top results to return"""
    how: str
    """How to calculate the similarity between the query and the documents."""

    def _get_relevant_documents(
        self,
        query: str,
        *, run_manager: CallbackManagerForRetrieverRun,  filter: Dict = None
    ) -> List[Document]:
        """Sync implementations for retriever."""
        search_vector = get_embeddings(query)
        result = self.aurora_cluster.similarity_search(
            search_vector, how=self.how, k=self.k, filter=filter
        )
        print (f"Query:{query} how={self.how}, k={self.k}, filter = {filter}")
        rows = json.loads(result.get("formattedRecords"))

        matching_documents = []

        for row in rows:
            metadata = json.loads(row.get("metadata"))
            metadata.update(content_type=row.get("content_type"),source=row.get("sourceurl"))
            
            document_kwargs = dict(id=row.get("id"), metadata=metadata)

            if self.how == "cosine": metadata.update(similarity=row.get("similarity"))
            elif self.how == "l2":metadata.update(distance=row.get("distance"))

            if row.get("content_type") == "text":
                matching_documents.append(
                    Document(page_content=row.get("chunks"), **document_kwargs)
                )
            if row.get("content_type") == "image":
                matching_documents.append(
                    Document(page_content=row.get("sourceurl"), **document_kwargs)
                )

        return matching_documents
