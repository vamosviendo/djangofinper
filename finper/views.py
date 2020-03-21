from django.shortcuts import render
from django.views import generic

from .models import Account, Movement


def index(request):
    return render(request, 'finper/index.html')


class MovListView(generic.ListView):
    template_name = 'finper/movements.html'
    context_object_name = 'movements_list'

    def get_queryset(self):
        return Movement.objects.order_by('-date')


class AccListView(generic.ListView):
    template_name = 'finper/accounts.html'
    context_object_name = 'accounts_list'

    def get_queryset(self):
        return Account.objects.order_by('name')


class MovDetailView(generic.DetailView):
    model = Movement
    template_name = 'finper/mov_detail.html'


class AccDetailView(generic.DetailView):
    model = Account
    template_name = 'finper/acc_detail.html'
