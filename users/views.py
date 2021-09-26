from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UserRegisterForm
from django_cassiopeia import cassiopeia as cass

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            form.save()
            messages.success(request, f"Your account has been created!")
            return redirect('login')

            
    else:
        form = UserRegisterForm()
    
    return render(request, 'users/register.html', {'form': form})