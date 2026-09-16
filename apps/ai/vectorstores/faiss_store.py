from pathlib import Path

import faiss
import numpy as np
from django.conf import settings


class FAISSVectorStore:
    """
    Persistent FAISS vector store.

    Uses normalized vectors + IndexFlatIP,
    which provides cosine-similarity search.
    """

    INDEX_FILENAME = "claims.index"

    def __init__(self):
        self.storage_dir = (
            Path(settings.BASE_DIR)
            / "storage"
            / "faiss"
        )

        self.storage_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.index_path = (
            self.storage_dir
            / self.INDEX_FILENAME
        )

        self.index = None

        self._load_index()

    def _load_index(self):
        if self.index_path.exists():
            self.index = faiss.read_index(
                str(self.index_path)
            )

    def _create_index(self, dimension: int):
        self.index = faiss.IndexIDMap(
            faiss.IndexFlatIP(dimension)
        )

    def add_vectors(
        self,
        vectors: list[list[float]],
        ids: list[int],
    ):
        if not vectors:
            return

        if len(vectors) != len(ids):
            raise ValueError(
                "Vectors and IDs must have "
                "the same length."
            )

        matrix = np.asarray(
            vectors,
            dtype="float32",
        )

        if matrix.ndim != 2:
            raise ValueError(
                "Vectors must be a 2D matrix."
            )

        if matrix.shape[0] != len(ids):
            raise ValueError(
                "Vector count does not match ID count."
            )

        faiss.normalize_L2(matrix)

        if self.index is None:
            self._create_index(
                matrix.shape[1]
            )

        if self.index.d != matrix.shape[1]:
            raise ValueError(
                "Embedding dimension does not match "
                "the existing FAISS index."
            )

        ids_array = np.asarray(
            ids,
            dtype="int64",
        )

        # Replace existing vectors with the
        # same IDs.
        self.index.remove_ids(ids_array)

        self.index.add_with_ids(
            matrix,
            ids_array,
        )

        self.save()

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
    ) -> list[dict]:
        """
        Search for the most similar vectors.
        """

        if self.index is None:
            return []

        if self.index.ntotal == 0:
            return []

        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        query = np.asarray(
            [query_vector],
            dtype="float32",
        )

        if query.ndim != 2:
            raise ValueError(
                "Query vector must be a 2D array."
            )

        if query.shape[1] != self.index.d:
            raise ValueError(
                "Query embedding dimension does not "
                "match the FAISS index."
            )

        faiss.normalize_L2(query)

        search_k = min(
            top_k,
            self.index.ntotal,
        )

        scores, ids = self.index.search(
            query,
            search_k,
        )

        results = []

        for score, index_id in zip(
            scores[0],
            ids[0],
        ):
            if index_id == -1:
                continue

            results.append(
                {
                    "faiss_index_id": int(
                        index_id
                    ),
                    "score": float(score),
                }
            )

        return results

    def save(self):
        if self.index is None:
            return

        faiss.write_index(
            self.index,
            str(self.index_path),
        )

    def count(self) -> int:
        if self.index is None:
            return 0

        return self.index.ntotal