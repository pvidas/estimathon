from django.contrib import admin

from .models import Game, Question, Team, Submission

admin.site.register(Game)
admin.site.register(Question)
admin.site.register(Team)
admin.site.register(Submission)