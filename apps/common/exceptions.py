class DomainError(Exception):
    """
    Base exception for business/domain errors.
    """

    default_message = "A business rule was violated."

    def __init__(self, message=None):
        self.message = message or self.default_message
        super().__init__(self.message)


class CustomerAlreadyExistsError(DomainError):
    default_message = "Customer already exists."


class CustomerNotFoundError(DomainError):
    default_message = "Customer was not found."


class PolicyValidationError(DomainError):
    default_message = "Policy validation failed."


class PolicyNotFoundError(DomainError):
    default_message = "Policy was not found."


class ClaimValidationError(DomainError):
    default_message = "Claim validation failed."


class ClaimNotFoundError(DomainError):
    default_message = "Claim was not found."