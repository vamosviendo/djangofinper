from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.views import generic

from nandotools import debug

from .errors import AccountError
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
    object_list = Movement.objects.order_by('date', 'pk')

    def get_queryset(self):
        return Movement.objects.order_by('date', 'pk')

    def get_context_data(self, *args, **kwargs):
        arguments = super(MovTableView, self).get_context_data(*args, **kwargs)
        arguments['title'] = 'Finanzas Personales - Planilla de movimientos'
        arguments['movements_list'] = Movement.objects.order_by('date', 'pk')
        arguments['accounts_list'] = Account.objects.order_by('name')
        arguments['accounts_sum'] = Account.objects.aggregate(Sum('balance'))
        arguments['accounts_start_sum'] = Account.objects.aggregate(Sum('balance_start'))
        return arguments

    def post(self, request, *args, **kwargs):
        return MovMultipleDelete.as_view()(request, *args, **kwargs)


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
    """
    |_django.vies.generic.detail.SingleObjectTemplateResponseMixin
    | |     - get_template_names()
    | |_django.views.generic.base.TemplateResponseMixin
    |
    |_django.views.generic.base.TemplateResponseMixin
    |       - template_name: str
    |       - template_engine: str
    |       - response_class: TemplateResponse
    |       - content_type: str
    |       - render_to_response(context, **response_kwargs) -> self.TemplateResponse()
    |       - get_template_names() -> list
    |
    |_django.views.generic.edit.BaseDeleteView
    | |_django.views.generic.edit.DeletionMixin
    | |_django.views.generic.detail.BaseDetailView
    |
    |_django.views.generic.edit.DeletionMixin
    |       - success_url: str
    |       - delete(request: HttpRequest, *args, **kwargs) -> HttpResponseRedirect()
    |       - get_success_url() -> str
    |
    |_django.views.generic.detail.BaseDetailView
    | |     - get(request: HttpRequest, *args. **kwargs) -> HttpResponse()
    | |_django.views.generic.detail.SingleObjectMixin
    | | |_django.views.generic.base.ContextMixin
    | |_django.views.generic.base.View
    |
    |_django.views.generic.detail.SingleObjectMixin
    | |     - model: Model
    | |     - queryset: QuerySet
    | |     - slug_field: str (default: 'slug')
    | |     - slug_url_kwarg: str (default: 'slug')
    | |     - pk_url_kwarg: str (default: 'pk')
    | |     - context_object_name: str
    | |     - query_pk_and_slug: bool (default: False)
    | |     - get_object(queryset=None) -> object
    | |     - get_queryset() -> QuerySet
    | |     - get_context_object_name(obj: object) -> str
    | |     - get_context_data(**kwargs) -> dict
    | |         {'object': self.object, 'context_object_name': get_context_object_name(), kwargs}
    | |     - get_slug_field: str (default: self.slug_field
    | |_django.views.generic.base.ContextMixin
    |       - extra_context: dict (default: None)
    |       - get_context_data(**kwargs) -> dict
    |
    |_django.views.generic.base.View
        - http_method_names: list
        - classmethod as_view(**initkwargs) -> view()
        - setup(request: HttpRequest, *args, **kwargs)
        - dispatch(request: HttpRequest, *args, **kwargs) -> HttpResponse()
        - http_method_not_allowed(request: HttpRequest, *args, **kwargs)
            -> HttpResponseNotAllowed()
        - options(request: HttpRequest, *args, **kwargs) ->HttpResponse()
    """
    model = Movement
    success_url = reverse_lazy('finper:mov_sheet')


class MovMultipleDelete(generic.edit.DeleteView):
    model = Movement
    template_name = 'movement_multiple_confirm_delete.html'
    success_url = reverse_lazy('finper:mov_sheet')
    object = None
    args = None
    kwargs = None

    def delete(self, request, *args, **kwargs):
        para_borrar = request.POST.getlist("mult_delete")
        success_url = self.success_url
        for num in para_borrar:
            Movement.objects.get(pk=num).delete()

        return HttpResponseRedirect(success_url)


