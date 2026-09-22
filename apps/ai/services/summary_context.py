class ClaimSummaryContextBuilder:
    @staticmethod
    def build_claim_data(claim) -> str:

        return f"""
Claim Number: {claim.claim_number}
Claim Type: {claim.claim_type}
Claim Status: {claim.status}
Incident Date: {claim.incident_date}
Claim Description: {claim.incident_description}
Estimated Loss: {claim.estimated_loss}
Approved Amount: {claim.approved_amount}
Submitted At: {claim.created_at}
"""

    @staticmethod
    def build_document_context(
        results: list[dict],
    ) -> str:

        if not results:
            return ""

        sections = []

        for index, result in enumerate(
            results,
            start=1,
        ):
            sections.append(
                f"""
[Document Source {index}]
Document: {result["document_name"]}
Document Type: {result["document_type"]}
Chunk Index: {result["chunk_index"]}
Content:
{result["text"]}
"""
            )

        return "\n".join(sections)

    @staticmethod
    def build_requirements_data(
        requirements: list[dict],
    ) -> str:

        if not requirements:
            return "No document requirements were configured."

        lines = []

        for requirement in requirements:
            lines.append(
                (
                    f"Document Type: "
                    f"{requirement['document_type']}\n"
                    f"Description: "
                    f"{requirement['description']}\n"
                    f"Required: "
                    f"{requirement['required']}\n"
                    f"Fulfilled: "
                    f"{requirement['fulfilled']}"
                )
            )

        return "\n\n".join(lines)
