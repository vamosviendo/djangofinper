from datetime import date

from django.db import models
from django.utils import timezone


class Account(models.Model):
    name = models.CharField(max_length=20, default='Cuenta')
    balance = models.FloatField(default=0.0)
    
    def __str__(self):
        return f'{self.name}: {self.balance}'
    

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
    amount = models.FloatField(default=0.0)
    direction = models.CharField(max_length = 1,
                                 choices =  [
                                     ('+', 'Entrada'),
                                     ('-', 'Salida'),
                                     ('=', 'Traspaso')
                                     ],
                                 )
    currency = models.CharField(max_length=3, default='$')
    account_out = models.ForeignKey(Account,
                                    on_delete = models.PROTECT,
                                    related_name = 'account_out',
                                    verbose_name = 'cuenta_de_salida',
                                    default = 1)
    account_in = models.ForeignKey(Account,
                                   on_delete = models.PROTECT,
                                   related_name = 'account_in',
                                   verbose_name = 'cuenta_de_entrada',
                                   default = 1)
    category = models.ForeignKey(Category, 
                                 on_delete = models.PROTECT,
                                 verbose_name = 'categoría_del_movimiento')
    
    class Meta:
        ordering = ['date']
    
    def __str__(self):
        return f'{self.date} - {self.concept}: {self.amount} {self.account_in}'
        pass
    
    def save(self, *args, **kwargs):
        if self.direction == '+':
            self.account_in.balance += self.amount
        elif self.direction == '-':
            self.account_out.balance -= self.amount
        elif self.direction == '=':
            self.account_in.balance += self.amount
            self.account_out.balance -= self.amount
        super(Movement, self).save(*args, **kwargs)
        self.account_in.save()
        self.account_out.save()
        