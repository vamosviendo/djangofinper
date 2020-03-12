from datetime import date
from decimal import Decimal

from django.db import models
from django.db.models.signals import post_save
from django.utils import timezone


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
    concept = models.CharField(max_length=20, default='Movimiento')
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
    
    keeper = None
    keepname = None
    
    class Meta:
        ordering = ['date']
    
    def __str__(self):
        return f'{self.date} - {self.concept}: {self.amount} {self.account_in}'
        pass
    
#     def __setattr__(self, attr, value):
#         
# #         # Poner el for por afuera e ir agregando elemento tras elemento, a ver si
# #         # así se arregla
# #         super(Movement, self).__setattr__(self.field_names, [field.name for field
# #                                                         in self._meta.concrete_fields]
# #                                                         if hasattr(self, '_meta') 
# #                                                         else [])
#         field_names = [field.name for field in self._meta.concrete_fields] \
#                         if hasattr(self, '_meta') else []
#         if attr in field_names and attr not in ('id'):
#             print('ok')
# #             super(Movement, self).__setattr__(self.keeper, getattr(self, attr))
# #            self.keeper = getattr(self, attr)
#         super(Movement, self).__setattr__(attr, value)
#          
# #         if name == 'amount':
# #             print(name, value)
#               #super(Movement, self).__setattr__(self.keeper, self.__dict__[name])
#               #self.keeper = self.__dict__[name]
# #         #self.keepname = name 
# #         super(Movement, self).__setattr__(name, value)
    
    def save(self, *args, **kwargs):
        if self.account_in is not None:
            self.account_in.balance_previous = self.account_in.balance
            self.account_in.balance += self.amount
            self.account_in.save()
        if self.account_out is not None:
            self.account_out.balance_previous = self.account_out.balance
            self.account_out.balance -= self.amount
            self.account_out.save()
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