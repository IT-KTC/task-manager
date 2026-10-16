from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login,logout
from django.contrib import messages

# Create your views here.



def logout_view(request):

    if request.method == "POST":

        logout(request)

        messages.success(
            request,
            "logout successfully"
        )

        return redirect("login")
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
