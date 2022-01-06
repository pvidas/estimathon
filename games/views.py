from django.contrib.auth import login
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render, get_object_or_404

from .forms import TeamRegistrationForm, SubmissionForm
from .models import Game
from .utils import is_registered, get_submit_context, get_submissions_context, get_scoreboard_context


# TODO Implement "notifications", e.g. here: "You must log in to see this page."
def index(request):
    if request.user.is_anonymous:
        return redirect('login')

    return render(request, 'games/index.html', {'teams': request.user.teams.all()})


def register(request, game_slug):
    game = get_object_or_404(Game, slug=game_slug)

    if is_registered(request.user, game):
        return redirect('games:dashboard', game_slug)

    if request.method == 'POST':
        form = TeamRegistrationForm(request.POST)
        if form.is_valid():
            team = form.save(commit=False)
            team.game = game
            try:
                team.full_clean()
                team.save()

                if request.user.is_anonymous:
                    username = f'{game_slug}_team_{game.teams.count()}'  # TODO This can fail!
                    new_user = team.members.create(username=username)
                    login(request, new_user)
                else:
                    team.members.add(request.user)

                return redirect('games:dashboard', game_slug)
            except ValidationError as e:
                form.add_error(field=None, error=e)
    else:
        form = TeamRegistrationForm()
    context = {
        'game': game,
        'form': form,
    }
    return render(request, 'games/register.html', context)


def dashboard(request, game_slug):
    game = get_object_or_404(Game, slug=game_slug)

    if not is_registered(request.user, game):
        return redirect('games:register', game_slug)

    team = request.user.teams.get(game=game)

    if request.method == 'POST':
        form = SubmissionForm(request.POST)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.team = team
            try:
                submission.full_clean()
                submission.save()
                return redirect('games:dashboard', game_slug)
            except ValidationError as e:
                form.add_error(field=None, error=e)
    else:
        form = None
    context = {
        'game': game,
        'team_name': team.team_name,
        'submit': get_submit_context(team, form, {'url': 'games:dashboard', 'args': game_slug}),
        'submissions': get_submissions_context(team),
        'scoreboard': get_scoreboard_context(game, highlight_team=team),
    }
    return render(request, 'games/dashboard.html', context)


def scoreboard(request, game_slug):
    game = get_object_or_404(Game, slug=game_slug)
    context = {
        'game': game,
        'scoreboard': get_scoreboard_context(game),
    }
    return render(request, 'games/scoreboard.html', context)
