from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone

DECIMAL_MAX_DIGITS = 65
DECIMAL_PLACES = 20


# TODO https://docs.djangoproject.com/en/4.0/ref/databases/#mysql-sql-mode

# TODO Admin action that generates a pdf with all questions.
# TODO Admin action that changes question positions to 1,2,3...
class Game(models.Model):
    slug = models.SlugField(primary_key=True)
    full_name = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    duration = models.DurationField()
    submission_limit = models.PositiveSmallIntegerField()
    is_open_for_registration = models.BooleanField(default=False)

    def __str__(self):
        return self.slug

    def get_absolute_url(self):
        return reverse('games:dashboard', kwargs={'game_slug': self.slug})
    
    @property
    def end_time(self):
        return self.start_time + self.duration
    
    @property
    def has_started(self):
        return self.start_time <= timezone.now()

    @property
    def has_ended(self):
        return self.end_time <= timezone.now()

    @property
    def is_running(self):
        return self.has_started and not self.has_ended
    

class Question(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='questions')
    statement = models.TextField()
    answer = models.DecimalField(max_digits=DECIMAL_MAX_DIGITS, decimal_places=DECIMAL_PLACES)
    position = models.PositiveSmallIntegerField()  # TODO Fill this automatically.

    class Meta:
        ordering = ['position']

    def __str__(self):
        return f'{self.position}. {self.statement}'

    # TODO This triggers on saving an already existing model as well...
    def validate_unique(self, exclude=None):
        super().validate_unique(exclude=exclude)
        if not exclude or ('game' not in exclude and 'position' not in exclude):
            if self.__class__.objects.filter(game=self.game, position=self.position).exists():
                raise ValidationError({'position': 'Question at this position already exists.'})


class Team(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='teams')
    members = models.ManyToManyField(User, related_name='teams')  # TODO User can't be in multiple teams in one game.
    team_name = models.CharField(max_length=50)

    def __str__(self):
        return self.team_name

    def validate_unique(self, exclude=None):
        super().validate_unique(exclude=exclude)
        if not exclude or ('game' not in exclude and 'team_name' not in exclude):
            if self.__class__.objects.filter(game=self.game, team_name=self.team_name).exists():
                raise ValidationError({'team_name': 'Team with this name already exists.'})


class Submission(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='submissions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='submissions')
    interval_lower_bound = models.DecimalField(max_digits=DECIMAL_MAX_DIGITS, decimal_places=DECIMAL_PLACES)
    interval_upper_bound = models.DecimalField(max_digits=DECIMAL_MAX_DIGITS, decimal_places=DECIMAL_PLACES)
    submission_time = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['submission_time']

    def __str__(self):
        return f'[{self.interval_lower_bound:.2E}, {self.interval_upper_bound:.2E}]'
    
    def clean_fields(self, exclude=None):
        super().clean_fields(exclude=exclude)

        errors = {}
        if not exclude or ('team' not in exclude and 'question' not in exclude):
            if self.team.game != self.question.game:
                errors['team'] = 'Team must be related to the same game as question.'
        if not exclude or 'interval_lower_bound' not in exclude:
            if self.interval_lower_bound <= 0:
                errors['interval_lower_bound'] = 'Lower bound must be positive.'
        if not exclude or 'interval_upper_bound' not in exclude:
            if self.interval_upper_bound <= 0:
                errors['interval_upper_bound'] = 'Upper bound must be positive.'
        
        if errors:
            raise ValidationError(errors)

    def clean(self):
        if self.interval_lower_bound is not None and self.interval_upper_bound is not None:
            if self.interval_lower_bound > self.interval_upper_bound:
                raise ValidationError('Interval must not be empty.')

    @property
    def interval_contains_answer(self):
        return self.interval_lower_bound <= self.question.answer <= self.interval_upper_bound
    
    @property
    def game(self):
        return self.question.game

    @property
    def interval_score(self):
        return self.interval_upper_bound // self.interval_lower_bound
    
    @property
    def submitted_during_game(self):
        return self.game.start_time <= self.submission_time < self.game.end_time

    @property
    def submitted_before_game(self):
        return self.submission_time < self.game.start_time

    @property
    def submitted_after_game(self):
        return self.submission_time >= self.game.end_time