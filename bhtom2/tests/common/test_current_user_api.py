from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from bhtom_custom_registration.bhtom_registration.models import LatexUser


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


class AdminUserApiTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.create_url = reverse('bhtom_common:admin_create_user_api')
        self.token_url = reverse('bhtom_common:admin_get_user_token_api')
        self.admin = User.objects.create_user(
            username='admin',
            password='secret',
            email='admin@example.org',
            is_staff=True,
        )
        self.admin_token, _ = Token.objects.get_or_create(user=self.admin)

    def authenticate_as_admin(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {self.admin_token.key}')

    def test_admin_can_create_user_with_generated_account(self):
        self.authenticate_as_admin()

        response = self.client.post(self.create_url, {
            'firstname': 'Jane',
            'surname': 'Doe',
            'email': 'jane@example.org',
            'affiliation': 'Observatory',
            'about': 'Observer account created by admin.',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        payload = response.json()
        self.assertEqual(payload['message'], 'User created successfully.')
        self.assertEqual(payload['username'], 'jane.doe')
        self.assertEqual(payload['email'], 'jane@example.org')
        self.assertNotIn('password', payload)
        self.assertTrue(payload['token'])

        user = User.objects.get(username='jane.doe')
        self.assertEqual(user.first_name, 'Jane')
        self.assertEqual(user.last_name, 'Doe')
        self.assertEqual(Token.objects.get(user=user).key, payload['token'])
        self.assertTrue(Group.objects.get(name='Public').user_set.filter(id=user.id).exists())

        profile = LatexUser.objects.get(user=user)
        self.assertEqual(profile.latex_affiliation, 'Observatory')
        self.assertEqual(profile.about_me, 'Observer account created by admin.')

    def test_non_admin_cannot_create_user(self):
        user = User.objects.create_user(username='regular', password='secret')
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        response = self.client.post(self.create_url, {
            'firstname': 'Jane',
            'surname': 'Doe',
            'email': 'jane@example.org',
            'about': 'Observer account created by admin.',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_user_duplicate_generated_username_returns_message(self):
        self.authenticate_as_admin()
        User.objects.create_user(username='jane.doe', password='secret')

        response = self.client.post(self.create_url, {
            'firstname': 'Jane',
            'surname': 'Doe',
            'email': 'jane@example.org',
            'about': 'Observer account created by admin.',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        payload = response.json()
        self.assertEqual(payload['Error'], 'Could not create user.')
        self.assertIn('username', payload['details'])
        self.assertIn("jane.doe", payload['details']['username'][0])

    def test_admin_can_get_user_token_by_username(self):
        self.authenticate_as_admin()
        user = User.objects.create_user(username='john.smith', password='secret')
        token, _ = Token.objects.get_or_create(user=user)

        response = self.client.post(self.token_url, {
            'username': 'john.smith',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {
            'id': user.id,
            'username': 'john.smith',
            'token': token.key,
        })

    def test_token_lookup_returns_404_for_missing_user(self):
        self.authenticate_as_admin()

        response = self.client.post(self.token_url, {
            'username': 'missing.user',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
