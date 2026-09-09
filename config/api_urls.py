from django.urls import include, path


urlpatterns = [
    path(
        "customers/",
        include(
            "apps.customers.urls",
        ),
    ),
    path(
        "policies/",
        include(
            "apps.policies.urls",
        ),
    ),
    path(
        "claims/",
        include(
            "apps.claims.urls",
        ),
    ),
]