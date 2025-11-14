from django.shortcuts import render, redirect, get_object_or_404
from .models import Show, Review
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.admin.views.decorators import staff_member_required
from django import forms
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import ReviewForm
from .models import Profile

def home(request):
    filter_type = request.GET.get('type')
    if filter_type in ['TV', 'Movie']:
        shows = Show.objects.filter(show_type=filter_type)
    else:
        shows = Show.objects.all()

    context = {
        'shows': shows,
        'filter_type': filter_type,
    }
    return render(request, 'recommendations/home.html', context)

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone_number = request.POST.get('phone_number')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
        else:
            user = User.objects.create_user(
                username=username,
                password=password1,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            Profile.objects.create(user=user, phone_number=phone_number)
            login(request, user)
            return redirect('/')

    return render(request, 'recommendations/signup.html')


def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)

        if user:
            login(request, user)
            return redirect('/')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'recommendations/login.html')

class ShowForm(forms.ModelForm):
    class Meta:
        model = Show
        fields = ['title', 'description', 'genre', 'show_type']
@staff_member_required
def add_show(request):
    if request.method == 'POST':
        form = ShowForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = ShowForm()
    return render(request, 'recommendations/add_show.html', {'form': form})

@login_required
def add_review(request, show_id):
    show = get_object_or_404(Show, id=show_id)

    # Prevent already-reviewed users from even accessing the form
    if Review.objects.filter(user=request.user, show=show).exists():
        messages.warning(request, "You have already reviewed this show.")
        reviews = Review.objects.filter(show=show)
        return render(request, 'recommendations/view_reviews.html', {'show': show, 'reviews': reviews})

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.show = show
            review.save()
            return redirect('view_reviews', show_id=show.id)
    else:
        form = ReviewForm()

    return render(request, 'recommendations/add_review.html', {'form': form, 'show': show})
@login_required
def edit_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    if review.user != request.user and not request.user.is_staff:
        messages.error(request, "You are not authorized to edit this review.")
        return redirect('view_reviews', show_id=review.show.id)

    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, "Review updated successfully.")
            return redirect('view_reviews', show_id=review.show.id)
    else:
        form = ReviewForm(instance=review)

    return render(request, 'recommendations/edit_review.html', {'form': form, 'review': review})


@login_required
def delete_review(request, review_id):
    review = get_object_or_404(Review, id=review_id)
    if review.user != request.user and not request.user.is_staff:
        messages.error(request, "You are not authorized to delete this review.")
        return redirect('view_reviews', show_id=review.show.id)

    if request.method == 'POST':
        show_id = review.show.id
        review.delete()
        messages.success(request, "Review deleted.")
        return redirect('view_reviews', show_id=show_id)

    return render(request, 'recommendations/confirm_delete.html', {'review': review})



def view_reviews(request, show_id):
    show = get_object_or_404(Show, id=show_id)
    reviews = Review.objects.filter(show=show)
    return render(request, 'recommendations/view_reviews.html', {'show': show, 'reviews': reviews})

def filter_by_genre(request, genre):
    shows = Show.objects.filter(genre__icontains=genre)
    return render(request, 'recommendations/home.html', {'shows': shows})


def search(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', 'all')

    if query:
        if category == 'title':
            shows = Show.objects.filter(title__icontains=query)
        elif category == 'genre':
            shows = Show.objects.filter(genre__icontains=query)
        else:  # all
            shows = Show.objects.filter(
                Q(title__icontains=query) |
                Q(genre__icontains=query)
            )
    else:
        shows = Show.objects.all()

    return render(request, 'recommendations/search_results.html', {
        'shows': shows,
        'query': query,
        'category': category
    })

def user_logout(request):
    logout(request)
    return redirect('/')