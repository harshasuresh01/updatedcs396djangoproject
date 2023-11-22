from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q

from .models import Quiz, Attempt, Question, Choice, StudentAnswer
from .forms import QuizForm, QuestionForm, ChoiceForm
from account.models import Account


def quiz_list(request):
    search_query = request.GET.get('q', '')  # Get the search term from the request

    if search_query:
        # Filter quizzes based on the search term and sort them alphabetically
        quizzes = Quiz.objects.filter(title__icontains=search_query).order_by('title')
    else:
        # Get all quizzes and sort them alphabetically
        quizzes = Quiz.objects.all().order_by('title')

    quizzes_with_attempts = []
    for quiz in quizzes:
        attempt = Attempt.objects.filter(quiz=quiz, student=request.user).order_by('-date_attempted').first()
        quizzes_with_attempts.append((quiz, attempt))

    return render(request, 'quizzes/quiz_list.html', {
        'quizzes_with_attempts': quizzes_with_attempts,
        'search_query': search_query,
        'on_quizzes_page': True  # Add this line
    })




@login_required
def quiz_detail(request, quiz_title):
    quiz = get_object_or_404(Quiz, title=quiz_title)
    user_account = Account.objects.get(email=request.user.email)

    def calculate_percentile(attempt):
        all_scores = Attempt.objects.filter(quiz=quiz).order_by('score')
        higher_scores = all_scores.filter(score__gt=attempt.score).count()
        percentile = (1 - higher_scores / all_scores.count()) * 100
        return round(percentile, 2)

    if user_account.is_teacher:
        student_attempts = Attempt.objects.filter(quiz=quiz).select_related('student')
        for attempt in student_attempts:
            attempt.percentile = calculate_percentile(attempt)
        context = {'quiz': quiz, 'student_attempts': student_attempts}
        return render(request, 'quizzes/quiz_detail_teacher.html', context)
    else:
        attempts = Attempt.objects.filter(quiz=quiz, student=request.user).order_by('-date_attempted')
        remaining_attempts = 3 - attempts.count()
        latest_attempt = attempts.first()

        if request.method == 'POST':
            if 'retake_quiz' in request.POST:
                return redirect('quizzes:quiz_detail', quiz_title=quiz.title)
            elif remaining_attempts > 0:
                score = 0
                for question in quiz.questions.all():
                    selected_choice_id = request.POST.get(f'question_{question.id}')
                    if selected_choice_id and question.choices.get(id=selected_choice_id).is_correct:
                        score += 1
                new_attempt = Attempt.objects.create(quiz=quiz, student=request.user, score=score)
                new_attempt.percentile = calculate_percentile(new_attempt)

                for question in quiz.questions.all():
                    selected_choice_id = request.POST.get(f'question_{question.id}')
                    if selected_choice_id:
                        selected_choice = Choice.objects.get(id=selected_choice_id)
                        StudentAnswer.objects.create(
                            attempt=new_attempt,
                            question=question,
                            choice=selected_choice
                        )

                context = {
                    'quiz': quiz,
                    'latest_attempt': new_attempt,
                    'remaining_attempts': 3 - Attempt.objects.filter(quiz=quiz, student=request.user).count(),
                    'max_attempts': 3
                }
                return render(request, 'quizzes/quiz_detail_student.html', context)
            else:
                context = {
                    'quiz': quiz,
                    'error': "You have already taken this quiz 3 times.",
                    'latest_attempt': latest_attempt,
                    'remaining_attempts': remaining_attempts,
                    'max_attempts': 3
                }
        else:
            context = {
                'quiz': quiz,
                'latest_attempt': latest_attempt,
                'remaining_attempts': remaining_attempts,
                'max_attempts': 3
            }
            return render(request, 'quizzes/quiz_detail_student.html', context)







@login_required
def create_quiz(request):
    if request.method == 'POST':
        quiz_form = QuizForm(request.POST)
        if quiz_form.is_valid():
            quiz = quiz_form.save(commit=False)
            quiz.created_by = request.user
            quiz.save()

            # Process each question
            for i in range(0, 100):  # Assuming a maximum of 100 questions for safety
                question_text = request.POST.get(f'questions-{i}-text')
                if not question_text:
                    break  # Break if no more questions are found

                question = Question.objects.create(quiz=quiz, text=question_text)

                # Process each choice for the question
                for j in range(4):  # Assuming 4 choices per question
                    choice_text = request.POST.get(f'questions-{i}-choice-{j}')
                    correct_choice = request.POST.get(f'questions-{i}-correct')
                    if choice_text:
                        is_correct = False
                        if correct_choice.isdigit():
                            is_correct = (j + 1) == int(correct_choice)
                        Choice.objects.create(
                            question=question,
                            text=choice_text,
                            is_correct=is_correct
                        )

            return redirect('quizzes:quiz_list')
        else:
            return render(request, 'quizzes/create_quiz.html', {'quiz_form': quiz_form})
    else:
        quiz_form = QuizForm()

    return render(request, 'quizzes/create_quiz.html', {'quiz_form': quiz_form})