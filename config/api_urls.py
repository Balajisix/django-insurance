from django.urls import include, path


urlpatterns = [
    path(
        "auth/",
        include("apps.users.urls"),
    ),
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
    path(
        "",
        include("apps.documents.urls"),
    ),
]