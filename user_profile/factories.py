import factory
from factory.django import DjangoModelFactory
from faker import Faker
from user_profile.models import User

fake = Faker()

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    email = factory.LazyAttribute(lambda _: fake.email())
    username = factory.LazyAttribute(lambda _: fake.user_name())
    password = factory.PostGenerationMethodCall('set_password', 'test_password')