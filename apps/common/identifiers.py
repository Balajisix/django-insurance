import uuid


def generate_business_number(prefix: str) -> str:

    unique_part = uuid.uuid4().hex[:12].upper()

    return f"{prefix}-{unique_part}"


def generate_customer_number() -> str:
    return generate_business_number("CUST")


def generate_policy_number() -> str:
    return generate_business_number("POL")


def generate_claim_number() -> str:
    return generate_business_number("CLM")