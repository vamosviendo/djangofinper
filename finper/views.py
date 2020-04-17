from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse, reverse_lazy
from django.views import generic

from .errors import AccountError
from .forms import MovementForm, MovementModelForm, AccountAddModelForm, AccountModModelForm
from .models import Account, Movement


def index(request):
    """ Página principal provisoria"""
    return render(request,
                  'finper/index.html',
                  {'title': 'Finanzas Personales - Página principal'})


def check_balance(request, pk):
    """ Verifica que el saldo de una cuenta sea igual al saldo inicial más
        la suma de sus movimientos de entrada menos la suma de sus movimientos
        de salida.
        Si la cuenta es correcta, muestra la vista detallada de la cuenta.
        De lo contrario, muestra una página con opciones de corrección del saldo
    """
    if Account.objects.get(pk=pk).check_balance()['saldoOk']:
        return HttpResponseRedirect(reverse('finper:accdetail', args=[pk]))
    else:
        print("error de saldo")
        return HttpResponseRedirect(reverse('finper:bal_error', args=[pk]))


def correct_balance(request, pk):
    """ Corrige el saldo final de una cuenta, basándose en el saldo inicial,
        sumando los movimientos de entrada y restando los de salida.
    """
    cuenta = Account.objects.get(pk=pk)
    cuenta.balance = cuenta.balance_start + cuenta.check_balance()['movsum']
    cuenta.save()
    return HttpResponseRedirect(reverse('finper:mov_sheet'))


def correct_start_balance(request, pk):
    """ Corrige el saldo inicial de una cuenta, basándose en el saldo final,
        restando los movimientos de entrada y sumando los de salida.
    """
    cuenta = Account.objects.get(pk=pk)
    cuenta.balance_start = cuenta.balance - cuenta.check_balance()['movsum']
    cuenta.save()
    return HttpResponseRedirect(reverse('finper:mov_sheet'))


def check_movements(request, pk):
    """ Ante una diferencia entre saldo inicial, movimientos y saldo final,
        permite corregir un movimiento erróneo.
        (La corrección de este movimiento no debería incidir en el saldo final,
        y no debería permitirse que sea una cifra distinta a la diferencia que
        se presenta)"""
    # TODO
    pass


def balance_error(request, pk):
    """ Muestra la plantilla balance_error.html, con opciones para la corrección
        de un saldo erróneo."""
    cta = Account.objects.get(pk=pk)
    return render(
        request,
        'finper/balance_error.html',
        {
            'request': request,
            'cta': cta,
        }
    )


###################
# Clases
###################


class AccListView(generic.ListView):
    """ Clase de vista de lista de cuentas """
    template_name = 'finper/accounts.html'
    context_object_name = 'accounts_list'

    def get_context_data(self, *args, object_list=None, **kwargs):
        data = super(AccListView, self).get_context_data(*args, **kwargs)
        data['title'] = 'Listado de cuentas'
        return data

    def get_queryset(self):
        return Account.objects.order_by('name')


class AccDetailView(generic.DetailView):
    """ Clase de vista de detalle de cuentas """
    model = Account
    template_name = 'finper/acc_detail.html'


class AccountCreate(generic.edit.CreateView):
    model = Account
    success_url = reverse_lazy('finper:mov_sheet')
    titulo = 'cuenta nueva'
    fields = ['codename', 'name', 'balance_start']


class AccountEdit(generic.edit.UpdateView):
    model = Account
    success_url = reverse_lazy('finper:mov_sheet')
    titulo = 'cuenta existente'
    fields = ['codename', 'name']


class AccountDelete(generic.edit.DeleteView):
    model = Account
    success_url = reverse_lazy('finper:mov_sheet')


class MovListView(generic.ListView):
    """ Clase de vista de lista de movimientos """
    template_name = 'finper/movements.html'
    context_object_name = 'movements_list'

    def get_context_data(self, *args, object_list=None, **kwargs):
        data = super(MovListView, self).get_context_data(*args, **kwargs)
        data['title'] = 'Listado de movimientos'
        return data

    def get_queryset(self):
        return Movement.objects.order_by('-date')


class MovTableView(generic.ListView):
    template_name = 'finper/mov_sheet.html'
    context_object_name = 'movements_table'

    def get_context_data(self, *args, **kwargs):
        arguments = super().get_context_data(*args, **kwargs)
        arguments['title'] = 'Finanzas Personales - Planilla de movimientos'
        arguments['movements_list'] = Movement.objects.order_by('date', 'pk')
        arguments['accounts_list'] = Account.objects.order_by('name')
        arguments['accounts_sum'] = Account.objects.aggregate(Sum('balance'))
        arguments['accounts_start_sum'] = Account.objects.aggregate(Sum('balance_start'))
        return arguments

    def get_queryset(self):
        return Movement.objects.order_by('date', 'pk')


class MovDetailView(generic.DetailView):
    """ Clase de vista de detalle de movimientos """
    model = Movement
    template_name = 'finper/mov_detail.html'


class MovCreate(generic.edit.CreateView):
    model = Movement
    success_url = reverse_lazy('finper:mov_sheet')
    fields = '__all__'

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except AccountError:
            messages.add_message(request, messages.ERROR,
                                 "Debe seleccionar al menos una cuenta de "
                                 "entrada o una cuenta de salida"
                                 )
            return render(request,
                          template_name=self.get_template_names(),
                          context=self.get_context_data())


class MovEdit(generic.edit.UpdateView):
    model = Movement
    success_url = reverse_lazy('finper:mov_sheet')
    fields = '__all__'

    def post(self, request, *args, **kwargs):
        try:
            return super().post(request, *args, **kwargs)
        except AccountError:
            messages.add_message(request, messages.ERROR,
                                 "Debe seleccionar al menos una cuenta de "
                                 "entrada o una cuenta de salida"
                                 )
            return render(request,
                          template_name=self.get_template_names(),
                          context=self.get_context_data())


class MovDelete(generic.edit.DeleteView):
    model = Movement
    success_url = reverse_lazy('finper:mov_sheet')
