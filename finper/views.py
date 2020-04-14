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


# Template: finper/mov_sheet.html
# url: movsheet/
def movsheet(request):
    """ Planilla de movimientos.
        Muestra la plantilla mov_sheet.html, con un detalle de los movimientos,
        su incidencia en las cuentas y el saldo final de cada cuenta y total. """
    movements_list = Movement.objects.order_by('date', 'pk')
    accounts_list = Account.objects.order_by('name')
    accounts_sums = Account.objects.aggregate(Sum('balance'), Sum('balance_start'))
    arguments = {
        'title': 'Finanzas Personales - Planilla de movimientos',
        'movements_list': movements_list,
        'accounts_list': accounts_list,
        'accounts_sum': accounts_sums['balance__sum'],
        'accounts_start_sum': accounts_sums['balance_start__sum'],
    }
    return render(request, 'finper/mov_sheet.html', arguments)


def add_movement_model(request):
    """ Añadir movimiento. Versión basada en ModelForm"""
    submitted = False
    if request.method == 'POST':
        form = MovementModelForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/finper/mov_sheet.html/?submitted=True')
    else:
        form = MovementModelForm()
        if 'submitted' in request.GET:
            submitted = True
    return render(request,
                  'finper/add_movement.html',
                  {'title': 'Finanzas Personales - Movimiento nuevo - ModelForm',
                   'form': form,
                   'submitted': submitted})


def add_movement(request):
    """ Añadir movimiento. Versión basada en formulario de campos individuales. """
    submitted = False
    if request.method == 'POST':
        form = MovementForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            mov = Movement(
                date=cd['date'],
                title=cd['title'],
                detail=cd['detail'],
                amount=cd['amount'],
                currency=cd['currency'],
                account_in=cd['account_in'],
                account_out=cd['account_out'],
                category=cd['category']
            )
            mov.save()
            return HttpResponseRedirect('/mov_sheet/')
    else:
        form = MovementForm()
        if 'submitted' in request.GET:
            submitted = True

    return render(
        request,
        'finper/add_movement.html',
        {'title': 'Finanzas Personales - Movimiento nuevo - No ModelForm',
         'form': form,
         'submitted': submitted}

    )


def add_account_model(request):
    """ Añadir cuenta nueva. Versión basada en ModelForm"""
    submitted = False
    if request.method == 'POST':
        form = AccountAddModelForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/mov_sheet/')
    else:
        form = AccountAddModelForm()
        if 'submitted' in request.GET:
            submitted = True
    return render(request,
                  'finper/add_account.html',
                  {'title': 'Finanzas Personales - Cuenta nueva - ModelForm',
                   'form': form,
                   'submitted': submitted})


def update_account(request, pk):
    acc_id = int(pk)

    try:
        acc_sel = Account.objects.get(id = acc_id)
    except Account.DoesNotExist:
        return HttpResponseRedirect('/mov_sheet/')

    form = AccountModModelForm(request.POST or None, instance=acc_sel)

    if form.is_valid():
        form.save()
        return HttpResponseRedirect('/mov_sheet/')

    return render(request,
                  'finper/add_account.html',
                  {'title': 'Finanzas Personales - Modificar cuenta - ModelForm',
                   'form': form,
                  })


def delete_account(request, pk):
    acc_id = int(pk)

    try:
        acc_sel = Account.objects.get(id=acc_id)
    except Account.DoesNotExist:
        return HttpResponseRedirect('/mov_sheet/')

    acc_sel.delete()
    return HttpResponseRedirect('/mov_sheet/')


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
