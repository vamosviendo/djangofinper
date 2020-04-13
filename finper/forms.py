from django import forms
from django.utils import timezone

from .models import Movement, Account, Category


# Añadir movimiento nuevo
# ModelForm
# View: add_movement
# Template: finper/add_movement.html
# url: add_movement_model
class MovementModelForm(forms.ModelForm):

    detail = forms.CharField(required=False)
    account_in = forms.ModelChoiceField(queryset=Account.objects.all(), required=False)
    account_out = forms.ModelChoiceField(queryset=Account.objects.all(), required=False)

    class Meta:
        model = Movement
        fields = '__all__'


# Añadir movimiento nuevo
# Form (no ModelForm)
# View: add_movement
# Template: finper/add_movement.html
# url: add_movement
class MovementForm(forms.Form):
    date = forms.DateField(label='Fecha', initial=timezone.now)
    title = forms.CharField(label='Concepto', max_length=20)
    detail = forms.CharField(label='Detalle', max_length=30, required=False)
    amount = forms.DecimalField(label='Monto')
    currency = forms.CharField(label='Moneda', max_length=3)
    account_in = forms.ModelChoiceField(
        queryset=Account.objects.all(),
        required=False,
        label='Cta. de entrada')
    account_out = forms.ModelChoiceField(
        queryset=Account.objects.all(),
        required=False,
        label='Cta. de salida')
    category = forms.ModelChoiceField(queryset=Category.objects.all(), label='Categoría')


# Añadir cuenta nueva
# ModelForm
# View: add_account
# Template: finper/add_account.html
# url: add_account
class AccountAddModelForm(forms.ModelForm):

    class Meta():
        model = Account
        fields = '__all__'


# Modificar cuenta
# (No permite modificar saldos, solamente nombres y otros datos)
# ModelForm
# View: add_account
# Template: finper/add_account.html
# url: add_account
class AccountModModelForm(forms.ModelForm):

    class Meta():
        model = Account
        fields = ['codename', 'name']
