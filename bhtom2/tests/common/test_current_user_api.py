from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient


class CurrentUserApiTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('bhtom_common:current_user_api')

    def test_authenticated_request_returns_current_user_payload(self):
        user = User.objects.create_user(
            username='jdoe',
            password='secret',
            first_name='Jane',
            last_name='Doe',
            email='jane@example.org'
        )
        token = Token.objects.create(user=user)

        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {
            'id': user.id,
            'username': 'jdoe',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@example.org',
        })

    def test_unauthenticated_request_returns_401(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
