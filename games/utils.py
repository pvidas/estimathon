from .forms import SubmissionForm


def is_registered(user, game):
    return not user.is_anonymous and user.teams.filter(game=game).exists()


def get_submit_context(team, form, form_action):
    n_submissions = team.submissions.filter(  # TODO Put this into a function, it's replicated three times already.
            submission_time__gte=team.game.start_time,
            submission_time__lt=team.game.end_time).count()
    return {
        'n_submissions_left': max(0, team.game.submission_limit - n_submissions),
        'form': form,
        'form_action': form_action,
    }


def get_submissions_context(team):
    submissions = [{'submission': submission} for submission in team.submissions.all()]
    submissions_remaining = team.game.submission_limit
    for item in submissions:
        submission = item['submission']
        if submission.submitted_before_game:
            item['status'] = 'Too early'
        elif submission.submitted_after_game:
            item['status'] = 'Too late'
        elif submissions_remaining == 0:
            item['status'] = 'Limit exceeded'
        else:
            submissions_remaining -= 1
            if submission.interval_contains_answer:
                item['status'] = 'Correct'
            else:
                item['status'] = 'Incorrect'
    submissions.reverse()
    return submissions


def get_scoreboard_context(game, highlight_team=None):
    teams = []
    for team in game.teams.all():
        submissions = list(team.submissions.filter(
            submission_time__gte=game.start_time,
            submission_time__lt=game.end_time,
        )[:game.submission_limit])

        results = []
        for question in game.questions.all():
            submissions_to_question = [submission for submission in submissions if submission.question == question]
            tries = len(submissions_to_question)
            if submissions_to_question:
                last_submission = submissions_to_question[-1]
                score = last_submission.interval_score if last_submission.interval_contains_answer else 0
            else:
                score = 0
            results.append({'score': score, 'tries': tries})

        bad_intervals = sum(result['score'] == 0 for result in results)
        interval_score_sum = sum(result['score'] for result in results)
        total_score = (10 + interval_score_sum) * 2**bad_intervals

        teams.append({
            'team_name': team.team_name,
            'results': results,
            'total_score': total_score,
            'highlight': team == highlight_team,
        })

    teams.sort(key=lambda team: (team['total_score'], team['team_name']))
    for i in range(len(teams)):
        if i > 0 and teams[i]['total_score'] == teams[i - 1]['total_score']:
            teams[i]['rank'] = teams[i - 1]['rank']
        else:
            teams[i]['rank'] = i + 1

    question_positions = game.questions.values_list('position', flat=True)

    return {
        'teams': teams,
        'question_positions': question_positions,
    }
