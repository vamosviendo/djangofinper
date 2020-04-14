from django.db import models
from django.db.models import Sum
from django.db.models.signals import post_save
from django.utils import timezone
from model_utils import FieldTracker

from .errors import AccountError

def valueorzero(param):
    if type(param) == type(None):
        return 0;
    else:
        return param


class Account(models.Model):
    codename = models.CharField(max_length=4, unique=True)
    name = models.CharField(max_length=20, default='Cuenta')
    balance_start = models.DecimalField(max_digits=15,
                                        decimal_places=2,
                                        default=0.0)
    balance_previous = models.DecimalField(max_digits=15,
                                           decimal_places=2,
                                           default=0.0)
    balance = models.DecimalField(max_digits=15,
                                  decimal_places=2,
                                  default=0.0)

    objects = models.Manager()

    def __str__(self):
        return f'{self.name}: {self.balance}'

    def reconnect(self):
        """ Devuelve el mismo objeto actualizado a partir de su clave primaria.
            Cuando una objeto Account, al ser reemplazado en un movimiento,
            pierde la conexión con el registro que le corresponde por su id,
            vuelve a conectarlo.
            Ignoro si hay un procedimiento estándar para resolver esto.
            Me resultó más rápido por el momento hacer esto que investigarlo"""
        return Account.objects.get(pk=self.pk)

    @classmethod
    def post_create(cls, sender, instance, created, *args, **kwargs):
        """ Cuando se crea un nuevo objeto Account, el saldo final debe ser igual
            al saldo inicial, y el saldo anterior al final debe ser 0.
            Esto debe suceder solamente cuando se lo crea, no cuando se lo modifica."""
        if not created:
            return

        instance.balance = instance.balance_start
        instance.balance_previous = 0
        instance.save()

    def check_balance(self):
        """ A partir del saldo inicial, sumar movimientos de entrada, restar
            movimientos de salida y comparar con el saldo final.
            Devolver True si la cuenta coincide, y False si no.
        """
        movsum = valueorzero(self.movements_in.aggregate(Sum('amount'))['amount__sum']) - \
                 valueorzero(self.movements_out.aggregate(Sum('amount'))['amount__sum'])
        balok = self.balance_start + movsum

        return {'saldoOk': self.balance == balok,
                'movsum': movsum}


post_save.connect(Account.post_create, sender=Account)


class Category(models.Model):
    name = models.CharField(max_length=30, default='Varios')
    description = models.CharField(max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


def _pkornone(account):
    """ Devuelve clave primaria de un objeto Account.
        Si account es None, devuelve None """
    if account is None:
        return None
    return account.pk


class Movement(models.Model):
    """ Movimiento de dinero (entrada, salida o traspaso)"""
    date = models.DateField('Fecha', default=timezone.now)
    title = models.CharField('Concepto', max_length=20, default='Movimiento')
    detail = models.CharField('Detalle', max_length=30, null=True, blank=True)
    amount = models.DecimalField('Monto',
                                 max_digits=15,
                                 decimal_places=2,
                                 default=0.0)
    currency = models.CharField('Moneda', max_length=3, default='$')
    account_out = models.ForeignKey(Account,
                                    on_delete=models.PROTECT,
                                    related_name='movements_out',
                                    verbose_name='cuenta_de_salida',
                                    null=True,
                                    blank=True)
    account_in = models.ForeignKey(Account,
                                   on_delete=models.PROTECT,
                                   related_name='movements_in',
                                   verbose_name='cuenta_de_entrada',
                                   null=True,
                                   blank=True)
    category = models.ForeignKey(Category,
                                 on_delete=models.PROTECT,
                                 verbose_name='categoría',
                                 )

    objects = models.Manager()

    tracker = FieldTracker(fields=['amount', 'account_in_id', 'account_out_id'])

    class Meta:
        ordering = ['date']

    def __str__(self):
        movstr = f'{self.date} - {self.title} - '
        movstr += f'{self.account_in.name}: {self.amount} ' if self.account_in is not None else ''
        movstr += f'{self.account_out.name}: {self.amount} ' if self.account_out is not None else ''
        return movstr

    def _prevaccount(self, accountid):
        """ Devuelve el objeto Account anterior tras un cambio de cuenta del
            movimiento. Si no hay una cuenta anterior, devuelve None"""
        if self.tracker.previous(accountid) is None:
            return None
        return Account.objects.get(id=self.tracker.previous(accountid))

    def save(self, *args, **kwargs):
        """ Al salvar un movimiento nuevo, se modifica el saldo de las cuentas
            referidas en account_in y account_out, si existen (Debe existir
            por lo menos una)."""

        # Si es un movimiento nuevo
        if self.pk is None:
            if self.account_in is None and self.account_out is None:
                # Alguna de las dos debe ser distinta de None
                raise AccountError('El movimiento no tiene cuenta de entrada ni de salida.')
            if self.account_in is not None:
                # Si es movimiento de entrada, sumar al saldo de account_in
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

            # Si cambia la cuenta de salida del movimiento
            oldaccountout = self._prevaccount('account_out_id') \
                if self.tracker.has_changed('account_out_id') \
                else self.account_out
            accountoutchanged = (oldaccountout != self.account_out)

            # Si cambia el monto del movimiento
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
                    if oldaccountin.pk == _pkornone(self.account_out):
                        self.account_out = oldaccountin.reconnect()

            if self.account_in is not None:
                self.account_in.balance += self.amount
                self.account_in.save()

                if self.account_in.pk == _pkornone(oldaccountout):
                    oldaccountout = self.account_in.reconnect()

            if oldaccountout is not None:
                oldaccountout.balance += oldamount
                if accountoutchanged:
                    oldaccountout.save()
                    if oldaccountout.pk == _pkornone(self.account_in):
                        self.account_in = oldaccountout.reconnect()

            if self.account_out is not None:
                self.account_out.balance -= self.amount
                self.account_out.save()

                if self.account_out.pk == _pkornone(oldaccountin):
                    oldaccountin = self.account_out.reconnect()

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
