from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from articles.models import Article
from django.shortcuts import render
from django.core.paginator import Paginator

@login_required
def home_view(request):
    articles = Article.objects.filter(is_published=True).order_by('-created_at')
    paginator = Paginator(articles, 5)  # 5 articles per page

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'home.html', {'page_obj': page_obj})

def about_view(request):
    return render(request, 'about.html')