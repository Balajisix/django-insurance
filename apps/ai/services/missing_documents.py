from apps.claims.models import ClaimDocumentRequirement


class MissingDocumentService:
    @staticmethod
    def get_required_document_status(
        *,
        claim_id: int,
    ) -> list[dict]:

        requirements = (
            ClaimDocumentRequirement.objects
            .filter(claim_id=claim_id)
            .order_by("document_type")
        )

        return [
            {
                "document_type": (
                    requirement.document_type
                ),
                "description": (
                    requirement.description
                ),
                "required": (
                    requirement.is_required
                ),
                "fulfilled": (
                    requirement.is_fulfilled
                ),
                "fulfilled_at": (
                    requirement.fulfilled_at
                ),
            }
            for requirement in requirements
        ]

    @staticmethod
    def get_missing_required_documents(
        *,
        claim_id: int,
    ) -> list[dict]:

        requirements = (
            ClaimDocumentRequirement.objects
            .filter(
                claim_id=claim_id,
                is_required=True,
                is_fulfilled=False,
            )
            .order_by("document_type")
        )

        return [
            {
                "document_type": (
                    requirement.document_type
                ),
                "description": (
                    requirement.description
                ),
            }
            for requirement in requirements
        ]
