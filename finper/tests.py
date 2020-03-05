from django.test import TestCase
from django.utils import timezone

from .models import Movement, Account, Category

def create_account(nombre):
    return Account.objects.create(name=nombre, balance=1000.0)
    
def create_category():
    return Category.objects.create(name='test', description='para pruebas')

def create_movement(cuenta_in, cuenta_out, direccion, monto=0.0):
    fecha = timezone.now()
    concepto = 'Movimiento de prueba'
    categoria = create_category()
    return Movement.objects.create(date = fecha, 
                                   concept = concepto, 
                                   amount = monto,
                                   direction = direccion,
                                   account_in = cuenta_in,
                                   account_out = cuenta_out,
                                   category = categoria)


# Create your tests here.
class MovementModelTest(TestCase):
    
    def test_save_with_output_movement(self):
        '''Test if at savign an output movement, the amount of the movement substracts
        itself from the Account balance'''
        acc = create_account(nombre='Account')
        saldo = acc.balance
        mov = create_movement(cuenta_in = acc, 
                              cuenta_out = acc, 
                              direccion = '-',
                              monto = 500)
        self.assertEqual(saldo, mov.account_out.balance + mov.amount)
    
    def test_save_with_input_movement(self):
        '''Test if at savign an input movement, the amount of the movement sums 
        itself to the Account balance'''
        acc = create_account(nombre='Account')
        saldo = acc.balance
        mov = create_movement(cuenta_in = acc, 
                              cuenta_out = acc,
                              direccion = '+', 
                              monto = 600)
        self.assertEqual(saldo, mov.account_in.balance - mov.amount)
    
    def test_save_with_transfer_movement(self):
        '''Comprueba que el monto de un movimiento de transferencia se resta de 
        una cuenta y se sume a otra.'''
        accin = create_account(nombre='Cuenta1')
        accout = create_account(nombre='Cuenta2')
        balin = accin.balance
        balout = accout.balance
        mov = create_movement(cuenta_in = accin, 
                              cuenta_out = accout,
                              direccion = '=', 
                              monto = 900)
        self.assertEqual((balin, balout), 
                         (mov.account_in.balance - mov.amount, 
                          mov.account_out.balance + mov.amount)
                         )
    
#     def test_objects_create_with_output_movement(self):
#         pass