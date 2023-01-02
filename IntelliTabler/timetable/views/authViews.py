from django.core.mail import EmailMessage
from django.contrib.auth import logout
from django.shortcuts import get_object_or_404, render, redirect
from ..forms import RegistrationForm
from ..models import User
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from ..tokens import account_activation_token
from django.contrib import messages

def register(request):
    context={}
    
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active=False
            user.save()
            current_site = get_current_site(request)
            mail_subject = 'Activate your blog account.'
            message = render_to_string('registration/acc_active_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':account_activation_token.make_token(user),
                'protocol': 'https' if request.is_secure() else 'http'
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(
                        mail_subject, message, to=[to_email]
            )
            if email.send():
                username = form.cleaned_data.get('username')
                messages.success(request, f"Dear <b>{username}")
            else:
                message.error(request, f'Problem sending email')
            return redirect('index')
        else:
            context["form"] = form
    else:
        form = RegistrationForm()
        context['form']=form
    return render(request, 'registration/register.html', context)

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        # return redirect('home')
        messages.success(request, 'Thank you for your email confirmation. Now you can login your account.')
        return redirect('login')
    else:
        messages.error(request, "Activation Link is Invalid")
        return redirect('index')

def logout_view(request):
    logout(request)
    messages(request, "You have been logged out")
    return redirect('index')


def successPage(request):
    if request.user.is_authenticated:
        messages.info(request, "You have succesfully logged in.")
        return redirect("departments")
    else:
        messages.info(request, "You have successfully Logged Out.")
    return render(request, 'index.html')
