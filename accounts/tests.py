import json

from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "login-rate-limit-tests",
        }
    },
    PASSWORD_HASHERS=[
        "django.contrib.auth.hashers.MD5PasswordHasher",
    ],
)
class LoginRateLimitTests(TestCase):

    def setUp(self):
        cache.clear()

    def test_html_login_is_rate_limited(self):
        url = reverse("login")

        for _ in range(5):
            response = self.client.post(
                url,
                {
                    "username": "unknown_user",
                    "password": "wrong_password",
                },
            )
            self.assertNotEqual(response.status_code, 429)

        response = self.client.post(
            url,
            {
                "username": "unknown_user",
                "password": "wrong_password",
            },
        )

        self.assertEqual(response.status_code, 429)

    def test_jwt_login_is_rate_limited(self):
        url = reverse("token_obtain_pair")

        payload = json.dumps({
            "username": "unknown_user",
            "password": "wrong_password",
        })

        for _ in range(5):
            response = self.client.post(
                url,
                data=payload,
                content_type="application/json",
            )
            self.assertNotEqual(response.status_code, 429)

        response = self.client.post(
            url,
            data=payload,
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 429)

    def test_html_and_jwt_share_limit(self):
        login_url = reverse("login")
        jwt_url = reverse("token_obtain_pair")

        for _ in range(3):
            self.client.post(
                login_url,
                {
                    "username": "unknown_user",
                    "password": "wrong_password",
                },
            )

        for _ in range(2):
            self.client.post(
                jwt_url,
                data=json.dumps({
                    "username": "unknown_user",
                    "password": "wrong_password",
                }),
                content_type="application/json",
            )

        response = self.client.post(
            jwt_url,
            data=json.dumps({
                "username": "unknown_user",
                "password": "wrong_password",
            }),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 429)