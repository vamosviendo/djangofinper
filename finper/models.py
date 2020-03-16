from datetime import date
from decimal import Decimal

from django.db import models
from django.db.models.signals import post_save
from django.utils import timezone
from model_utils import FieldTracker


class Account(models.Model):
    name = models.CharField(max_length=20, default='Cuenta')

    balance_start = models.DecimalField(max_digits = 15, 
                                        decimal_places = 2, 
                                        default = 0.0)
    balance_previous = models.DecimalField(max_digits = 15, 
                                         decimal_places = 2, 
                                         default = 0.0)
    balance = models.DecimalField(max_digits = 15, 
                                decimal_places = 2, 
                                default = 0.0)
    
    def __str__(self):
        return f'{self.name}: {self.balance}'
    
    def connect(self):
        ''' Cuando una objeto Account pierde la conexión con el registro
            que le corresponde por su id, vuelve a conectarlo. Ignoro si 
            hay un procedimiento estándar para resolver esto. Me resultó
            más rápido por el momento hacer esto que investigarlo'''
        return Account.objects.get(pk=self.pk)
    
    @classmethod
    def post_create(cls, sender, instance, created, *args, **kwargs):
        ''' Cuando se crea un nuevo objeto Account, el saldo final debe ser igual
            al saldo inicial, y el saldo anterior al final debe ser 0.
            Esto debe suceder solamente cuando se lo crea, no cuando se lo modifica.'''
        if not created:
            return

        instance.balance = instance.balance_start
        instance.balance_previous = 0
        instance.save()
        
post_save.connect(Account.post_create, sender = Account)


class Category(models.Model):
    name = models.CharField(max_length=30, default='Varios')
    description = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering=['name']


class Movement(models.Model):
    ''' Refleja un movimiento de dinero (entrada o salida)'''
    date = models.DateField(default=timezone.now)
    title = models.CharField(max_length=20, default='Movimiento')
    detail = models.CharField(max_length=30)
    amount = models.DecimalField(max_digits = 15, 
                                 decimal_places = 2, 
                                 default=0.0)
    currency = models.CharField(max_length=3, default='$')
    account_out = models.ForeignKey(Account,
                                    on_delete = models.PROTECT,
                                    related_name = 'movements_out',
                                    verbose_name = 'cuenta_de_salida',
                                    null = True)
    account_in = models.ForeignKey(Account,
                                   on_delete = models.PROTECT,
                                   related_name = 'movements_in',
                                   verbose_name = 'cuenta_de_entrada',
                                   null = True)
    category = models.ForeignKey(Category, 
                                 on_delete = models.PROTECT,
                                 verbose_name = 'categoría_del_movimiento')
    
    tracker = FieldTracker(fields=['amount', 'account_in_id', 'account_out_id'])
    
    class Meta:
        ordering = ['date']
    
#     def __init__(self, *args, **kwargs):
#         super(Movement, self).__init__(*args, **kwargs)
#         self.keeper = None
    
    def __str__(self):
        return f'{self.date} - {self.title}: {self.amount} {self.account_in}'
        pass
    
    def _prevaccount(self, accountid):
        if self.tracker.previous(accountid) is None:
            return None
        return Account.objects.get(id=self.tracker.previous(accountid)) \
            
    def _pkornone(self, account):
        if account is None:
            return None
        return account.pk 

    def save(self, *args, **kwargs):
        ''' Al salvar un movimiento nuevo, se modifica el saldo de las cuentas
            referidas en account_in y account_out, si existen (Debe existir 
            por lo menos una.'''
        
        # Si es un movimiento nuevo
        if self.pk is None:
            if self.account_in is None and self.account_out is None:
                # Alguna de las dos debe ser distinta de None
                raise Exception('El movimiento no tiene cuenta de entrada ni de salida.')
            if self.account_in is not None:
                # Si es movimientod de entrada, sumar al saldo de account_in
                self.account_in.balance_previous = self.account_in.balance
                self.account_in.balance += self.amount
                self.account_in.save()
            if self.account_out is not None:
                # Si es movimiento de salida, restar del saldo de account_out
                self.account_out.balance_previous = self.account_out.balance
                self.account_out.balance -= self.amount
                self.account_out.save()
                
        # Si se está modificando un movimiento ya cargado
        else:
            # Si cambia la cuenta de entrada del movimiento
            oldaccountin = self._prevaccount('account_in_id') \
                if self.tracker.has_changed('account_in_id') \
                else self.account_in
            accountinchanged = (oldaccountin != self.account_in)

            oldaccountout = self._prevaccount('account_out_id') \
                if self.tracker.has_changed('account_out_id') \
                else self.account_out
            accountoutchanged = (oldaccountout != self.account_out)

            oldamount = self.tracker.previous('amount') \
                if self.tracker.has_changed('amount') \
                else self.amount
                
            if oldaccountin is not None:
                oldaccountin.balance -= oldamount
                if accountinchanged:
                    oldaccountin.save()
                    '''
                    Acá se arma un brete cuando la vieja cuenta de entrada es la 
                    nueva cuenta de salida. 
                    Lo que sucede es lo siguiente:
                    - se resta el viejo monto de la vieja cuenta de entrada
                    - se salva la vieja cuenta de entrada (id = 1)
                    - self.account_out también tiene id 1 pero no registra el 
                      cambio producido en el saldo de la cuenta con id 1. 
                      Sigue manteniendo el saldo de antes del cambio de cuenta.
                      Es necesario 'reconectar' oldaccountin y self.account_out.
                      Lo mismo pasa en todas las otras posibilidades 
                    '''
                    
                    if oldaccountin.pk == self._pkornone(self.account_out):
                        self.account_out = Account.objects.get(pk=oldaccountin.pk)

            if self.account_in is not None:
                self.account_in.balance += self.amount
                self.account_in.save()
                
                if self.account_in.pk == self._pkornone(oldaccountout):
                    oldaccountout = Account.objects.get(pk=self.account_in.pk)
                
            if oldaccountout is not None:
                oldaccountout.balance += oldamount
                if accountoutchanged: 
                    oldaccountout.save()
                    if oldaccountout.pk == self._pkornone(self.account_in):
                        self.account_in = Account.objects.get(pk=oldaccountout.pk)
                        
            if self.account_out is not None:
                self.account_out.balance -= self.amount
                self.account_out.save()
                
                if self.account_out.pk == self._pkornone(oldaccountin):
                    oldaccountin = Account.objects.get(pk=self.account_out.pk)
        
        super(Movement, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.account_in is not None:
            self.account_in.balance_previous = self.account_in.balance
            self.account_in.balance -= self.amount
            self.account_in.save()
        if self.account_out is not None:
            self.account_out.balance_previous = self.account_out.balance
            self.account_out.balance += self.amount
            self.account_out.save()
        super(Movement, self).delete(*args, **kwargs)