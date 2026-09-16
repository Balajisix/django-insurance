from pathlib import Path

import faiss
import numpy as np
from django.conf import settings


class FAISSVectorStore:
    """
    FAISS vector store for semantic similarity search.

    We use:
        IndexFlatIP

    with normalized vectors, which gives cosine similarity.
    """

    INDEX_FILENAME = "claims.index"

    def __init__(self):
        self.storage_dir = Path(
            settings.BASE_DIR
        ) / "storage" / "faiss"

        self.storage_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.index_path = (
            self.storage_dir /
            self.INDEX_FILENAME
        )

        self.index = None

        self._load_index()

    def _load_index(self):
        if self.index_path.exists():
            self.index = faiss.read_index(
                str(self.index_path)
            )

    def _create_index(
        self,
        dimension: int,
    ):
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

        faiss.normalize_L2(matrix)

        if self.index is None:
            self._create_index(
                matrix.shape[1]
            )

        self.index.add_with_ids(
            matrix,
            np.asarray(
                ids,
                dtype="int64",
            ),
        )

        self.save()

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
    ):
        if self.index is None:
            return []

        query = np.asarray(
            [query_vector],
            dtype="float32",
        )

        faiss.normalize_L2(query)

        scores, ids = self.index.search(
            query,
            top_k,
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
                    "faiss_index_id": int(index_id),
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