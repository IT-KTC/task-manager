from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class UserAPITest(APITestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username="user1",
            password="12345678",
            email="user1@example.com",
        )

        self.other_user = User.objects.create_user(
            username="user2",
            password="12345678",
            email="user2@example.com",
        )

        self.admin = User.objects.create_user(
            username="admin",
            password="12345678",
            is_staff=True,
        )

    def test_me_requires_authentication(self):

        url = reverse("user-me")

        response = self.client.get(url)

        self.assertIn(
            response.status_code,
            [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN,
            ]
        )

    def test_user_can_view_own_profile(self):

        self.client.force_authenticate(
            user=self.user
        )

        url = reverse("user-me")

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["username"],
            "user1"
        )

    def test_user_can_update_own_profile(self):

        self.client.force_authenticate(
            user=self.user
        )

        url = reverse("user-me")

        response = self.client.patch(
            url,
            {
                "first_name": "Nguyen",
                "last_name": "An",
                "email": "new@example.com",
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.first_name,
            "Nguyen"
        )

        self.assertEqual(
            self.user.email,
            "new@example.com"
        )

    def test_user_cannot_change_username(self):

        self.client.force_authenticate(
            user=self.user
        )

        url = reverse("user-me")

        response = self.client.patch(
            url,
            {
                "username": "hacker_name"
            },
            format="json"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.user.refresh_from_db()

        self.assertEqual(
            self.user.username,
            "user1"
        )

    def test_normal_user_cannot_list_users(self):

        self.client.force_authenticate(
            user=self.user
        )

        url = reverse("user-list")

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )

    def test_admin_can_list_users(self):

        self.client.force_authenticate(
            user=self.admin
        )

        url = reverse("user-list")

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["count"],
            3
        )

    def test_admin_can_view_user_detail(self):

        self.client.force_authenticate(
            user=self.admin
        )

        url = reverse(
            "user-detail",
            kwargs={
                "pk": self.user.pk
            }
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK
        )

        self.assertEqual(
            response.data["username"],
            "user1"
        )

    def test_normal_user_cannot_view_other_user_detail(self):

        self.client.force_authenticate(
            user=self.user
        )

        url = reverse(
            "user-detail",
            kwargs={
                "pk": self.other_user.pk
            }
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN
        )