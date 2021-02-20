from django.db import IntegrityError
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView
from .models import User, Circle, Story
from .forms import RegisterForm

@login_required
def index(request):
    """The Write page where a user can start or join a Circle"""
    return render(request, 'circle/index.html', {
        "open_circles": Circle.open_circles.all(),
        "waiting_circles": Circle.waiting_circles.order_by('creation_time')
    })

class CircleView(LoginRequiredMixin, DetailView):
    """The Circle page for working on a story interactively. Template includes
    script that initiates websocket connection"""
    model = Circle
    context_object_name = 'circle'
    template_name = 'circle/circle.html'

def index_redirect(request):
    """Redirect to the Write page"""
    return HttpResponseRedirect(reverse("index"))

class FinishedStoryListView(LoginRequiredMixin, ListView):
    """Read page with list of all finished stories"""
    model = Story
    template_name = "circle/finishedstory_list.html"
    queryset = Story.objects.filter(finished=True).order_by('-finish_time')
    context_object_name = 'stories'

class FinishedStoryView(LoginRequiredMixin, DetailView):
    """Page for individual finished story, displays text and authors"""
    model = Story
    template_name = "circle/finishedstory_detail.html"
    queryset = Story.objects.filter(finished=True)
    context_object_name = 'story'

class UserDetailView(LoginRequiredMixin, DetailView):
    """User profile page"""
    model = User
    context_object_name = 'detail_user'

def login_view(request):
    """Displays or processes a log-in form"""
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
    """Register a new user"""
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
    else:
        form = RegisterForm()
    return render(request, "circle/register.html", {'form': form})

def logout_view(request):
    """Log a user out"""
    logout(request)
    return HttpResponseRedirect(reverse("login"))

