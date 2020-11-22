from django.db.models import Count
from django.shortcuts import render, get_object_or_404
from django.contrib.postgres.search import SearchVector
from .forms import CommentForm, SearchForm
from .models import Category, Product, Comment
from caart.forms import CartAddProductForm
from .recommender import Recommender


def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    return render(request, 'shop/product/list.html',
                  {'category': category,
                   'categories': categories,
                   'products': products})


def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)

    cart_product_form = CartAddProductForm()

    r = Recommender()
    recommended_products = r.suggest_products_for([product], 4)

    comments = product.comments.filter(active=True)
    print(comments, "HEllo")

    new_comment = None

    if request.method == 'POST':
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.product = product
            new_comment.user = request.user
            new_comment.name = request.user.first_name
            new_comment.save()
    else:
        comment_form = CommentForm()

    product_tags_ids = product.tags.values_list('id', flat=True)
    similar_products = Product.objects.filter(tags__in=product_tags_ids).exclude(id=product.id)

    similar_products = similar_products.annotate(same_tags=Count('tags')) \
                           .order_by('-same_tags', )[:4]

    return render(request, 'shop/product/detail.html', {'product': product,
                                                        'cart_product_form': cart_product_form,
                                                        'recommended_products': recommended_products,
                                                        'comment_form': comment_form,
                                                        'comments': comments,
                                                        'new_comment': new_comment,
                                                        'similar_products': similar_products,
                                                        })


def product_search(request):
    form = SearchForm()
    query = None
    results = []

    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            results = Product.objects.annotate(
                search=SearchVector('name','description'),
            ).filter(search=query)
    return render(request,'shop/product/search.html',{
                      'form': form,
                      'query' : query,
                      'results' : results,
                  })