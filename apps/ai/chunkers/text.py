class TextChunker:
    """
    Splits extracted text into overlapping chunks.

    Default:
        chunk_size = 1000 characters
        overlap = 200 characters
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        overlap: int = 200,
    ):
        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than zero."
            )

        if overlap < 0:
            raise ValueError(
                "overlap cannot be negative."
            )

        if overlap >= chunk_size:
            raise ValueError(
                "overlap must be smaller than chunk_size."
            )

        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(self, text: str) -> list[dict]:
        """
        Split text into overlapping chunks.

        Returns:
            [
                {
                    "chunk_index": 0,
                    "text": "...",
                    "start_character": 0,
                    "end_character": 1000,
                },
                ...
            ]
        """

        if not text:
            return []

        normalized_text = text.strip()

        if not normalized_text:
            return []

        chunks = []

        text_length = len(normalized_text)

        start = 0
        chunk_index = 0

        while start < text_length:
            end = min(
                start + self.chunk_size,
                text_length,
            )

            chunk_text = normalized_text[
                start:end
            ].strip()

            if chunk_text:
                chunks.append(
                    {
                        "chunk_index": chunk_index,
                        "text": chunk_text,
                        "start_character": start,
                        "end_character": end,
                    }
                )

                chunk_index += 1

            if end >= text_length:
                break

            start = end - self.overlap

        return chunks