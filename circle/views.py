from django.db import IntegrityError
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import DetailView
from .models import User, FinishedStory, WorkingStory

@login_required
def index(request):
    return render(request, 'circle/index.html')
    # TODO: We need a list of working stories that need authors
    # This will maybe connect up with a circle view? Yes I think so. We can 
    # redirect to it from the index
    #return render(request, 'circle/circle.html')

@login_required
def circle_view(request, pk):
    return render(request, 'circle/circle.html', {
    })

class CircleView(LoginRequiredMixin, DetailView):
    model = WorkingStory
    context_object_name = 'story'
    template_name = 'circle/circle.html'

def index_redirect(request):
    return HttpResponseRedirect(reverse("index"))

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(request.POST["next_url"])
        else:
            return render(request, "circle/login.html", {
                "next_url": request.POST["next_url"],
                "message": "Invalid username and/or password."
            })
    else:
        redirect = (True if "next" in request.GET else False)
        next_url = request.GET.get("next", default=reverse('index'))
        return render(request, "circle/login.html", {
            "next_url": next_url,
            "redirect": redirect,
        })

def register_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "circle/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "circle/register.html", {
                "message": "Something went wrong; possibly that username is already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "circle/register.html")

class FinishedStoryView(LoginRequiredMixin, DetailView):
    model = FinishedStory
    context_object_name = 'story'

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("login"))

