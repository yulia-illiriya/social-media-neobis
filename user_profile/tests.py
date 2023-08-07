from django.test import TestCase
from user_profile.factories import UserFactory
from django.urls import reverse
from django.core import mail
from rest_framework.test import APIClient
from django.test import RequestFactory
from unittest.mock import patch
from .services import *

import pytest

@pytest.fixture
def client():
    return APIClient()

@pytest.mark.django_db
@patch('django.core.mail.send_mail')
def test_send_email_verification(mock_send_mail):
    email = 'test@example.com'
    user = UserFactory(email=email)
    request = RequestFactory().get('/')
    request.session = {'verification_data': {'email': email, 'code': 1234}}   

    response = send_email_verification(request, email)
    assert response.status_code == 302 
    
    mock_send_mail.assert_called_once_with(
        'Код подтверждения был отправлен вам с сайта threads-neobis. Если вы получили это письмо по ошибке, проигнорируйте его',
        f'Ваш код подтверждения: {request.session["verification_data"]["code"]}',
        'your_email@example.com',
        [email],
        fail_silently=False,
    )
    
    

@pytest.mark.django_db
def test_verify_valid_code(client):
    email = 'test@example.com'
    code = 1234
    user = UserFactory(email=email)

    client.session['verification_data'] = {'email': email, 'code': code}

    # Отправляем POST-запрос с верным кодом подтверждения
    response = client.post(reverse('verify'), {'verification_code': code})
    assert response.status_code == 302  # Проверяем, что запрос перенаправлен

    # Проверяем, что пользователь помечен как подтвержденный
    user.refresh_from_db()
    assert user.is_validated

@pytest.mark.django_db
def test_verify_invalid_code(client):
    email = 'test@example.com'
    code = 1234

    # Создаем пользователя с указанным email с помощью фабрики
    user = UserFactory(email=email)

    # Устанавливаем в сессию верные данные подтверждения
    client.session['verification_data'] = {'email': email, 'code': code}

    # Отправляем POST-запрос с неверным кодом подтверждения
    response = client.post(reverse('verify'), {'verification_code': code + 1})
    assert response.status_code == 400 

