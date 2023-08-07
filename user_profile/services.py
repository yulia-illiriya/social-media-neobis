import random
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from .models import User

def send_email_verification(request, email):
    code = random.randint(1000, 9999)
    
    send_mail(
        'Код подтверждения был отправлен вам с сайта threads-neobis. Если вы получили это письмо по ошибке, проигнорируйте его',
        f'Ваш код подтверждения: {code}',
        'your_email@example.com',
        [email],
        fail_silently=False,
    )
    
    request.session['verification_data'] = {'email': email, 'code': code}
       
    return redirect('verify')


@require_POST
def verify(request):
    entered_code = request.POST.get('verification_code')    

    # Получаем сохраненные в сессии почту и код подтверждения
    verification_data = request.session.get('verification_data')
    email = verification_data.get('email')
    code = verification_data.get('code')

    if entered_code == code:
        
        try:            
            user = User.objects.get(email=email)            
            user.is_validated = True
            user.save()
        except User.DoesNotExist:
            return Response({"error": "Юзер не найден"}, status=400)        
        
    else:
          return APIException("Код введен неверно", code=400)       

    return redirect('home') 