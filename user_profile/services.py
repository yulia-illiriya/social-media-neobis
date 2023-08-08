# import random
# from django.core.mail import send_mail
# from django.shortcuts import redirect
# from django.urls import reverse
# from django.views.decorators.http import require_POST
# from rest_framework.response import Response
# from rest_framework.exceptions import APIException
# from config import settings
# from .models import User

# def send_email_verification(request, email):
#     code = random.randint(1000, 9999)
    
#     send_mail(
#         f'Введите код {code} для восстановления пароля. Если вы получили это письмо по ошибке, проигнорируйте его',       
#         [email],
#         fail_silently=False,
#     )
    
#     request.session['verification_data'] = {'email': email, 'code': code}
       
#     return redirect('verify')

# def send_password_reset_email(request):
#     if request.method == 'POST':
#         email = request.POST.get('email')
#         user = User.objects.get(email=email)

#         if user:            
#             code = random.randint(1000, 9999)
#             user.password_reset_code = code
#             user.save()

#             # Send the code to the user's email
#             subject = 'Password Reset Code'
#             message = f'Ваш код для восстановления пароля - {code}. Если вы получили это письмо по ошибке, проигнорируйте его'
#             from_email = settings.EMAIL_HOST_USER 
#             recipient_list = [email]
#             send_mail(subject, message, from_email, recipient_list, fail_silently=False)

#             return JsonResponse({'message': 'Password reset code sent successfully.'})
#         else:
#             return JsonResponse({'error': 'User with this email does not exist.'}, status=404)

#     return JsonResponse({'error': 'Invalid request method.'}, status=400)



# @require_POST
# def verify(request):
#     entered_code = request.POST.get('verification_code')    

#     # Получаем сохраненные в сессии почту и код подтверждения
#     verification_data = request.session.get('verification_data')
#     email = verification_data.get('email')
#     code = verification_data.get('code')

#     if entered_code == code:
        
#         return redirect('home')  
        
#     else:
#           return APIException("Код введен неверно", code=400)       

#     return redirect('home') 