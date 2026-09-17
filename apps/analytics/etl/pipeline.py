from apps.analytics.etl.extract import PostgreSQLExtractor
from apps.analytics.etl.load import SnowflakeLoader
from apps.analytics.etl.transform import SnowflakeTransformer


class SnowflakeETLPipeline:

    def __init__(self):
        # Create instances
        self.extractor = PostgreSQLExtractor()
        self.transformer = SnowflakeTransformer()
        self.loader = SnowflakeLoader()

    @staticmethod
    def normalize_key(series):
        return (
            series
            .astype("string")
            .str.strip()
            .str.upper()
        )

    def run(self):

        print()
        print("Starting PostgreSQL → Snowflake ETL...")
        print("=" * 80)

        # 1. EXTRACT
        customers = self.extractor.customers()
        policies = self.extractor.policies()
        claims = self.extractor.claims()
        settlements = self.extractor.settlements()
        ai_analyses = self.extractor.ai_analyses()

        print()
        print("Extracted rows:")
        print(f"Customers   : {len(customers)}")
        print(f"Policies    : {len(policies)}")
        print(f"Claims      : {len(claims)}")
        print(f"Settlements : {len(settlements)}")
        print(f"AI Analyses : {len(ai_analyses)}")

        # VALIDATE EXTRACTION
        if claims.empty:
            raise ValueError(
                "No claims found in PostgreSQL."
            )

        required_claim_columns = [
            "CLAIM_NUMBER",
            "POLICY_NUMBER",
            "CUSTOMER_NUMBER",
            "CLAIM_TYPE_CODE",
        ]

        missing_columns = [
            column
            for column in required_claim_columns
            if column not in claims.columns
        ]

        if missing_columns:
            raise ValueError(
                "Claims extraction is missing columns: "
                f"{missing_columns}"
            )

        print()
        print("Claim extraction preview:")
        print(
            claims[
                [
                    "CLAIM_NUMBER",
                    "POLICY_NUMBER",
                    "CUSTOMER_NUMBER",
                    "CLAIM_TYPE_CODE",
                ]
            ].to_string(index=False)
        )

        # VALIDATE BUSINESS KEYS
        if claims["CUSTOMER_NUMBER"].isna().any():

            missing_claims = claims.loc[
                claims["CUSTOMER_NUMBER"].isna(),
                "CLAIM_NUMBER",
            ].tolist()

            raise ValueError(
                "CUSTOMER_NUMBER is missing for claims: "
                f"{missing_claims}"
            )

        if claims["POLICY_NUMBER"].isna().any():

            missing_claims = claims.loc[
                claims["POLICY_NUMBER"].isna(),
                "CLAIM_NUMBER",
            ].tolist()

            raise ValueError(
                "POLICY_NUMBER is missing for claims: "
                f"{missing_claims}"
            )

        if claims["CLAIM_TYPE_CODE"].isna().any():

            missing_claims = claims.loc[
                claims["CLAIM_TYPE_CODE"].isna(),
                "CLAIM_NUMBER",
            ].tolist()

            raise ValueError(
                "CLAIM_TYPE_CODE is missing for claims: "
                f"{missing_claims}"
            )

        # 2. TRANSFORM
        dim_customer = self.transformer.dim_customer(
            customers
        )

        dim_policy = self.transformer.dim_policy(
            policies
        )

        fact_claim = self.transformer.fact_claim(
            claims=claims,
            settlements=settlements,
            ai_analyses=ai_analyses,
        )

        # 3. NORMALIZE BUSINESS KEYS
        for dataframe, columns in [
            (
                dim_customer,
                ["CUSTOMER_NUMBER"],
            ),
            (
                dim_policy,
                ["CUSTOMER_NUMBER", "POLICY_NUMBER"],
            ),
            (
                fact_claim,
                [
                    "CUSTOMER_NUMBER",
                    "POLICY_NUMBER",
                    "CLAIM_TYPE_CODE",
                ],
            ),
        ]:

            for column in columns:
                dataframe[column] = self.normalize_key(
                    dataframe[column]
                )

        # 4. FULL REFRESH
        self.loader.truncate_warehouse()

        # 5. LOAD DIMENSIONS
        self.loader.load_dim_customer(
            dim_customer
        )

        self.loader.load_dim_policy(
            dim_policy
        )

        # 6. GET SURROGATE KEYS
        customer_keys = self.loader.get_customer_keys()
        policy_keys = self.loader.get_policy_keys()
        claim_type_keys = self.loader.get_claim_type_keys()

        # Normalize Snowflake result column names
        customer_keys.columns = [
            str(column).upper()
            for column in customer_keys.columns
        ]

        policy_keys.columns = [
            str(column).upper()
            for column in policy_keys.columns
        ]

        claim_type_keys.columns = [
            str(column).upper()
            for column in claim_type_keys.columns
        ]

        # Normalize keys themselves
        customer_keys["CUSTOMER_NUMBER"] = (
            self.normalize_key(
                customer_keys["CUSTOMER_NUMBER"]
            )
        )

        policy_keys["POLICY_NUMBER"] = (
            self.normalize_key(
                policy_keys["POLICY_NUMBER"]
            )
        )

        claim_type_keys["CLAIM_TYPE_CODE"] = (
            self.normalize_key(
                claim_type_keys["CLAIM_TYPE_CODE"]
            )
        )

        # 7. CUSTOMER NUMBER -> CUSTOMER KEY
        print()
        print("Snowflake CUSTOMER mapping:")
        print(
            customer_keys[
                [
                    "CUSTOMER_KEY",
                    "CUSTOMER_NUMBER",
                ]
            ].to_string(index=False)
        )

        fact_claim = fact_claim.merge(
            customer_keys[
                [
                    "CUSTOMER_NUMBER",
                    "CUSTOMER_KEY",
                ]
            ],
            on="CUSTOMER_NUMBER",
            how="left",
        )

        # 8. POLICY NUMBER -> POLICY KEY
        fact_claim = fact_claim.merge(
            policy_keys[
                [
                    "POLICY_NUMBER",
                    "POLICY_KEY",
                ]
            ],
            on="POLICY_NUMBER",
            how="left",
        )

        # 9. CLAIM TYPE -> CLAIM TYPE KEY
        fact_claim = fact_claim.merge(
            claim_type_keys[
                [
                    "CLAIM_TYPE_CODE",
                    "CLAIM_TYPE_KEY",
                ]
            ],
            on="CLAIM_TYPE_CODE",
            how="left",
        )

        # 10. VALIDATE SURROGATE KEYS
        missing_customer_keys = fact_claim[
            fact_claim["CUSTOMER_KEY"].isna()
        ]

        if not missing_customer_keys.empty:

            print()
            print("CUSTOMER KEY MAPPING FAILED:")
            print(
                missing_customer_keys[
                    [
                        "CLAIM_NUMBER",
                        "CUSTOMER_NUMBER",
                    ]
                ].to_string(index=False)
            )

            raise ValueError(
                "Unable to map CUSTOMER_KEY for claims: "
                f"{missing_customer_keys['CLAIM_NUMBER'].tolist()}"
            )

        missing_policy_keys = fact_claim[
            fact_claim["POLICY_KEY"].isna()
        ]

        if not missing_policy_keys.empty:

            print()
            print("POLICY KEY MAPPING FAILED:")
            print(
                missing_policy_keys[
                    [
                        "CLAIM_NUMBER",
                        "POLICY_NUMBER",
                    ]
                ].to_string(index=False)
            )

            raise ValueError(
                "Unable to map POLICY_KEY for claims: "
                f"{missing_policy_keys['CLAIM_NUMBER'].tolist()}"
            )

        missing_claim_type_keys = fact_claim[
            fact_claim["CLAIM_TYPE_KEY"].isna()
        ]

        if not missing_claim_type_keys.empty:

            print()
            print("CLAIM TYPE KEY MAPPING FAILED:")
            print(
                missing_claim_type_keys[
                    [
                        "CLAIM_NUMBER",
                        "CLAIM_TYPE_CODE",
                    ]
                ].to_string(index=False)
            )

            raise ValueError(
                "Unable to map CLAIM_TYPE_KEY for claims: "
                f"{missing_claim_type_keys['CLAIM_NUMBER'].tolist()}"
            )

        # 11. CONVERT SURROGATE KEYS
        fact_claim["CUSTOMER_KEY"] = (
            fact_claim["CUSTOMER_KEY"].astype(int)
        )

        fact_claim["POLICY_KEY"] = (
            fact_claim["POLICY_KEY"].astype(int)
        )

        fact_claim["CLAIM_TYPE_KEY"] = (
            fact_claim["CLAIM_TYPE_KEY"].astype(int)
        )

        # 12. LOAD FACT
        self.loader.load_fact_claim(
            fact_claim
        )

        print()
        print("=" * 80)
        print("PostgreSQL → Snowflake ETL completed successfully.")
        print("=" * 80)

        return {
            "customers": len(dim_customer),
            "policies": len(dim_policy),
            "claims": len(fact_claim),
        }