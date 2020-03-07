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
    
    def test_output_movement_substracts(self):
        '''Test if at savign an output movement, the amount of the movement substracts
        itself from the Account balance'''
        acc = create_account(nombre='Account')
        saldo = acc.balance
        mov = create_movement(cuenta_in = acc, 
                              cuenta_out = acc, 
                              direccion = '-',
                              monto = 500)
        self.assertEqual(saldo, mov.account_out.balance + mov.amount)
    
    def test_input_movement_adds(self):
        '''Test if at savign an input movement, the amount of the movement sums 
        itself to the Account balance'''
        acc = create_account(nombre='Account')
        saldo = acc.balance
        mov = create_movement(cuenta_in = acc, 
                              cuenta_out = acc,
                              direccion = '+', 
                              monto = 600)
        self.assertEqual(saldo, mov.account_in.balance - mov.amount)
    
    def test_transfer_movement_transfers(self):
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
        
    def test_input_movement_goes_to_account_in(self):
        '''Comprueba que un movimiento de entrada (direction="+"), tiene
        un valor en Movement.account_in'''
        pass
    
    def test_input_movement_doesnt_go_to_account_out(self):
        '''Comprueba que un movimiento de entrada (direction="+"), no tiene
        un valor en Movement.account_out'''
        pass
    
    def test_output_movement_goes_to_account_out(self):
        '''Comprueba que un movimiento de salida (direction="-"), tiene
        un valor en Movement.account_out'''
        pass
    
    def test_output_movement_doesnt_go_to_account_in(self):
        '''Comprueba que un movimiento de salida (direction="-"), no tiene
        un valor en Movement.account_in'''
        pass
    
    def test_transfer_movement_goes_to_account_in_and_out(self):
        '''Comprueba que un movimiento de traspaso (direction="="), tiene
        un valor tanto en Movement.account_in como en Movement.account_out'''
        pass
    
    def test_transfer_movement_account_in_and_out_different(self):
        '''Comprueba que un movimiento de traspaso no tenga el mismo valor
        en Movement.account_in y Movement.account_out'''
        pass
    
    def test_movement_has_at_least_one_account_foreginkey(self):
        ''' Comprueba que un movimiento no tenga vacíos tanto el campos
            account_in como el campo account_out. Al menos uno de ellos debe
            tener un valor.'''
        pass
    
class AccountClassTest(TestCase):
    
    def test_input_movement_goes_to_movements_in(self):
        pass
    
    def test_input_movement_doesnt_go_to_movements_out(self):
        pass
    
    def test_output_movement_goes_to_movements_out(self):
        pass
    
    def test_output_movement_doesnt_go_to_movements_in(self):
        pass
    
    def test_transfer_movement_goes_to_movements_in_and_out(self):
        pass

    def test_final_balance_against_initial_balance(self):
        ''' Comprueba que el saldo final de cada cuenta coincide con el saldo 
            inicial al que se le han aplicado los movimientos
        '''
        pass
    
    