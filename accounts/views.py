from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.shortcuts import redirect, render

from .security import login_rate_limit

# Create your views here.



def logout_view(request):

    if request.method == "POST":

        logout(request)

        messages.success(
            request,
            "logout successfully"
        )

        return redirect("login")
@login_rate_limit
def login_view(request):
    if request.method == "POST": 
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid(): 
            user = form.get_user()
            login(request,user)
            messages.success(
                request,
                "login successfully"
            )
            return redirect("task_list")
    else: 
        form = AuthenticationForm()
    return render(
        request,
        "accounts/login.html",
        {
            "form": form
        }
    )


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"OK")
            return redirect("login")
    else: 
        form = UserCreationForm()

    context = {
        "form": form
    }
    return render(request, "accounts/register.html", context)
