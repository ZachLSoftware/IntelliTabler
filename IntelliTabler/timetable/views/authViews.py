from django.core.mail import EmailMessage
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from ..forms import RegistrationForm, changePassword, passwordResetForm
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
            mail_subject = 'Activate your IntelliTabler account.'
            message = render_to_string('auth_templates/acc_active_email.html', {
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
                messages.success(request, f"{username}, Please check your email for to confirm your account.")
            else:
                message.error(request, f'Problem sending email')
            return redirect('login')
        else:
            context["form"] = form
    else:
        form = RegistrationForm()
        context['form']=form
    return render(request, 'auth_templates/register.html', context)

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
        return redirect("dashboard")
    else:
        messages.info(request, "You have successfully Logged Out.")
    return render(request, 'index.html')


def passwordReset(request):
    if request.method=="POST":
        form = passwordResetForm(request.POST)
        if form.is_valid():
            user_email = form.cleaned_data['email']
            user= User.objects.filter(email=user_email).first()
            if user:
                current_site = get_current_site(request)
                mail_subject = 'Reset your IntelliTabler account password.'
                message = render_to_string('auth_templates/custom_password_reset_email.html', {
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
                    pass
                else:
                    message.error(request, f'Problem sending email')
        messages.success(request, "If your account exists, you will recieve a link to reset your password.")
        return redirect('login')
    form = passwordResetForm()
    return render(request, "auth_templates/password_reset.html", {"form":form})


def passwordResetConfirm(request, uidb64, token):
    uid = force_str(urlsafe_base64_decode(uidb64))
    try:
        user = User.objects.get(pk=uid)
    except:
        user= None
    if user is not None and account_activation_token.check_token(user, token):
        if request.method=='POST':
            form = changePassword(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Your password has been reset")
                return redirect('login')
        else:
            form = changePassword(user)
        return render(request, 'auth_templates/password_reset_form.html', {'form':form})
    else:
        messages.error(request, "Link was invalid")
        return redirect('login')

