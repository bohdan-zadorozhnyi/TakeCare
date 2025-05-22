from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import user_passes_test, login_required, permission_required
from .models import Article
from .forms import ArticleForm
from accounts.models import User, AdminProfile

def is_admin(user):
    return user.is_authenticated and user.role == 'ADMIN'

@permission_required('articles.list_article', raise_exception=True)
def article_list(request):
    articles = Article.objects.all().order_by('-created_at')
    return render(request, 'articles/article_list.html', {'articles': articles})

@permission_required('articles.add_article', raise_exception=True)
def article_create(request):
    if request.method == 'POST':
        form = ArticleForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.save()
            return redirect('articles:article_list')
    else:
        form = ArticleForm()
    return render(request, 'articles/article_form.html', {'form': form, 'action': 'Create'})

@permission_required('articles.change_article', raise_exception=True)
def article_edit(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if request.method == 'POST':
        form = ArticleForm(request.POST, instance=article)
        if form.is_valid():
            form.save()
            return redirect('articles:article_list')
    else:
        form = ArticleForm(instance=article)
    return render(request, 'articles/article_form.html', {'form': form, 'action': 'Edit'})

@permission_required('articles.delete_article', raise_exception=True)
def article_delete(request, pk):
    article = get_object_or_404(Article, pk=pk)
    if request.method == 'POST':
        article.delete()
        return redirect('articles:article_list')
    return render(request, 'articles/article_confirm_delete.html', {'article': article})

@login_required
@permission_required('articles.view_article', raise_exception=True)
def article_detail_view(request, article_id):
    article = get_object_or_404(Article, id=article_id)
    return render(request, 'articles/article_detail.html', {'article': article})