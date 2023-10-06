from .models import Activity
from user_profile.models import User

def create_activity(user, event_type, message=None):
    """
    Создать объект Activity при подписке или отправке запроса на подписку.
    """
    print(user, type(user))
    Activity.objects.create(user=user, event_type=event_type, message=message)



