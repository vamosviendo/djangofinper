# Template: finper/mov_sheet.html
# url: movsheet/
# Reemplazado por: class MovTableView
from django.db.models import Sum
from django.http import HttpResponseRedirect
from django.shortcuts import render

from finper.forms import MovementModelForm, MovementForm
from finper.models import Movement, Account


# Reemplazada por class MovTableView(generic.ListView)
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


# Reemplazada por class MovCreate(generic.edit.CreateView)
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


# Reemplazada por class MovCreate(generic.edit.CreateView)
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


# Reemplazada por AccountCreate(generic.edit.CreateView)
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


# Reemplazada por AccountEdit(generic.edit.UpdateView)
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


# Reemplazada por AccountDelete(generic.edit.DeleteView)
def delete_account(request, pk):
    acc_id = int(pk)

    try:
        acc_sel = Account.objects.get(id=acc_id)
    except Account.DoesNotExist:
        return HttpResponseRedirect('/mov_sheet/')

    acc_sel.delete()
    return HttpResponseRedirect('/mov_sheet/')


