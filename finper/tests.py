import decimal
import random

from django.test import TestCase
from django.utils import timezone

from .models import Movement, Account, Category

def create_account(nombre, saldo_inicial):
    return Account.objects.create(name=nombre, balance_start=saldo_inicial)
    
def create_category():
    return Category.objects.create(name='test', description='para pruebas')

def create_movement(cuenta_in=None, cuenta_out=None, monto=0):
    fecha = timezone.now()
    concepto = 'Movimiento de prueba'
    categoria = create_category()
    return Movement.objects.create(date = fecha, 
                                   concept = concepto, 
                                   amount = monto,
                                   account_in = cuenta_in,
                                   account_out = cuenta_out,
                                   category = categoria)


# Create your tests here.
class MovementModelTest(TestCase):
    ''' Pruebas para el modelo Movement'''
    
    def test_output_movement_substracts(self):
        '''Test if at savign an output movement, the amount of the movement substracts
        itself from the Account balance'''
        acc = create_account(nombre='Account', saldo_inicial = 5000)
        saldo = acc.balance
        mov = create_movement(cuenta_out = acc, 
                              monto = 500)
        self.assertEqual(saldo, mov.account_out.balance + mov.amount)
    
    def test_input_movement_adds(self):
        '''Test if at savign an input movement, the amount of the movement sums 
        itself to the Account balance'''
        acc = create_account(nombre='Account', saldo_inicial = 1200)
        saldo = acc.balance
        mov = create_movement(cuenta_in = acc, 
                              monto = 600)
        self.assertEqual(saldo, mov.account_in.balance - mov.amount)
    
    def test_transfer_movement_adds_and_substracts(self):
        '''Comprueba que el monto de un movimiento de transferencia se resta de 
        una cuenta y se sume a otra.'''
        accin = create_account(nombre='Cuenta1', saldo_inicial = 2000)
        accout = create_account(nombre='Cuenta2', saldo_inicial = 4500)
        balin = accin.balance
        balout = accout.balance
        mov = create_movement(cuenta_in = accin, 
                              cuenta_out = accout,
                              monto = 900)
        self.assertEqual((balin, balout), 
                         (mov.account_in.balance - mov.amount, 
                          mov.account_out.balance + mov.amount)
                         )
        
    def test_input_movement_doesnt_go_to_account_out(self):
        '''Comprueba que un movimiento de entrada (direction="+"), no tiene
        un valor en Movement.account_out'''
        accin = create_account(nombre='Cuenta', saldo_inicial = 4500)
        mov = create_movement(cuenta_in = accin, monto = 800)
        self.assertIsNone(mov.account_out)
    
    def test_output_movement_doesnt_go_to_account_in(self):
        '''Comprueba que un movimiento de salida (direction="-"), no tiene
        un valor en Movement.account_in'''
        accout = create_account(nombre='Cuenta', saldo_inicial = 4500)
        mov = create_movement(cuenta_out = accout, monto = 800)
        self.assertIsNone(mov.account_in)
    
    def test_transfer_movement_account_in_and_out_different(self):
        '''Comprueba que un movimiento de traspaso no tenga el mismo valor
        en Movement.account_in y Movement.account_out'''
        accin = create_account(nombre='Cuenta1', saldo_inicial = 2000)
        accout = create_account(nombre='Cuenta2', saldo_inicial = 4500)
        mov = create_movement(cuenta_in = accin, cuenta_out = accout,
                              monto = 900)
        self.assertNotEqual(mov.account_in, mov.account_out)
    
    def test_movement_has_at_least_one_account_foreginkey(self):
        ''' Comprueba que un movimiento no tenga vacíos tanto el campos
            account_in como el campo account_out. Al menos uno de ellos debe
            tener un valor.'''
        acc = create_account(nombre='Account', saldo_inicial = 1200)
        mov = create_movement(cuenta_in = acc, monto=100)
        self.assertTrue(mov.account_in is not None or mov.account_out is not None)
    
class AccountModelTest(TestCase):
    ''' Pruebas para el modelo Account'''
    
    def test_account_creation_sets_balance_to_balance_start(self):
        ''' Al crearse una cuenta nueva, balance y balance_start deben
            ser iguales.'''
        acc = create_account(nombre='Account', saldo_inicial = 1200)
        self.assertEqual(acc.balance_start, acc.balance)
    
    def test_account_creation_sets_balance_previous_to_zero(self):
        ''' Al crearse una cuenta nueva, balance_previous debe ser igual a 0'''
        acc = create_account(nombre='Account', saldo_inicial = 1200)
        self.assertEqual(acc.balance_previous, 0)
        
    def test_account_saving_does_not_set_balance_to_balance_start(self):
        ''' Al salvar modificaciones a una cuenta, no deben producirse
            los eventos asociados a su creación'''
        acc = create_account(nombre='Account', saldo_inicial = 1200)
        mov = create_movement(cuenta_in = acc, monto=100)
        acc.name = 'Cuenta'
        acc.save()
        self.assertNotEqual(acc.balance_start, acc.balance)
        
    def test_account_saving_does_not_set_balance_previous_to_zero(self):
        ''' Al salvar modificaciones a una cuenta, no deben producirse
            los eventos asociados a su creación'''
        acc = create_account(nombre='Account', saldo_inicial = 1200)
        mov = create_movement(cuenta_in = acc, monto=100)
        acc.name = 'Cuenta'
        acc.save()
        self.assertNotEqual(acc.balance_previous, 0)
        
    def test_input_movement_goes_to_movements_in(self):
        ''' Al ingresar un movimiento de entrada asociado a una cuenta, éste
            debe agregarse a la lista de movimientos de entrada de la cuenta'''
        acc = create_account(nombre='Account', saldo_inicial = 1200)
        mov = create_movement(cuenta_in = acc, monto=100)
        self.assertIs(acc.movements_in.count(), 1)
    
    def test_input_movement_doesnt_go_to_movements_out(self):
        ''' Al ingresar un movimiento de entrada asociado a una cuenta, éste
            NO debe agregarse a la lista de movimientos de salida de la cuenta'''
        acc = create_account(nombre='Account', saldo_inicial = 1200)
        mov = create_movement(cuenta_in = acc, monto=100)
        self.assertIs(acc.movements_out.count(), 0)
    
    def test_output_movement_goes_to_movements_out(self):
        ''' Al ingresar un movimiento de salida asociado a una cuenta, éste
            debe agregarse a la lista de movimientos de salida de la cuenta'''
        acc = create_account(nombre='Account', saldo_inicial = 1200)
        mov = create_movement(cuenta_out = acc, monto=100)
        self.assertIs(acc.movements_out.count(), 1)
    
    def test_output_movement_doesnt_go_to_movements_in(self):
        ''' Al ingresar un movimiento de salida asociado a una cuenta, éste
            NO debe agregarse a la lista de movimientos de entrada de la cuenta'''
        acc = create_account(nombre='Account', saldo_inicial = 1200)
        mov = create_movement(cuenta_out = acc, monto=100)
        self.assertIs(acc.movements_in.count(), 0)
    
    def test_transfer_movement_goes_to_movements_in_in_account_in(self):
        ''' Al ingresar un movimiento de transferencia de una cuenta a otra, éste
            debe agregarse a la lista de movimientos de entrada de la cuenta de
            entrada.'''
        accin = create_account(nombre='Account1', saldo_inicial = 1200)
        accout = create_account(nombre='Account2', saldo_inicial = 800)
        mov = create_movement(cuenta_in = accin, cuenta_out = accout, monto=100)
        self.assertIs(accin.movements_in.count(), 1)

    def test_transfer_movement_doesnt_go_to_movements_out_in_account_in(self):
        ''' Al ingresar un movimiento de transferencia de una cuenta a otra, éste
            NO debe agregarse a la lista de movimientos de salida de la cuenta de
            entrada.'''
        accin = create_account(nombre='Account1', saldo_inicial = 1200)
        accout = create_account(nombre='Account2', saldo_inicial = 800)
        mov = create_movement(cuenta_in = accin, cuenta_out = accout, monto=100)
        self.assertIs(accin.movements_out.count(), 0)

    def test_transfer_movement_goes_to_movements_out_in_account_out(self):
        ''' Al ingresar un movimiento de transferencia de una cuenta a otra, éste
            debe agregarse a la lista de movimientos de salida de la cuenta de
            salida.'''
        accin = create_account(nombre='Account1', saldo_inicial = 1200)
        accout = create_account(nombre='Account2', saldo_inicial = 800)
        mov = create_movement(cuenta_in = accin, cuenta_out = accout, monto=100)
        self.assertIs(accout.movements_out.count(), 1)

    def test_transfer_movement_doesnt_go_to_movements_in_in_account_out(self):
        ''' Al ingresar un movimiento de transferencia de una cuenta a otra, éste
            NO debe agregarse a la lista de movimientos de entrada de la cuenta de
            salida.'''
        accin = create_account(nombre='Account1', saldo_inicial = 1200)
        accout = create_account(nombre='Account2', saldo_inicial = 800)
        mov = create_movement(cuenta_in = accin, cuenta_out = accout, monto=100)
        self.assertIs(accout.movements_in.count(), 0)

    def test_input_movement_adds_to_balance(self):
        ''' Todo movimiento de entrada debe sumarse al saldo de la cuenta asociada
        '''
        acc = create_account(nombre='Account', saldo_inicial = 1200)
        mov = create_movement(cuenta_in = acc, monto=100)
        self.assertEqual(acc.balance, 1300)
    

    def test_output_movement_substracts_from_balance(self):
        ''' Todo movimiento de salida debe restarse del saldo de la cuenta asociada
        '''
        acc = create_account(nombre='Account', saldo_inicial = 1200)
        mov = create_movement(cuenta_out = acc, monto=100)
        self.assertEqual(acc.balance, 1100)
    
    
    def test_transfer_movement_adds_to_balance_in_account_in(self):
        ''' Todo movimiento de traspaso entre dos cuentas debe sumarse al saldo 
            de la cuenta de entrada asociada'''
        accin = create_account(nombre='Account1', saldo_inicial = 1200)
        accout = create_account(nombre='Account2', saldo_inicial = 800)
        mov = create_movement(cuenta_in = accin, cuenta_out = accout, monto=100)
        self.assertEqual(accin.balance, 1300)

    def test_transfer_movement_substracts_from_balance_in_account_out(self):
        ''' Todo movimiento de traspaso entre dos cuentas debe restarse del saldo 
            de la cuenta de salida asociada'''
        accin = create_account(nombre='Account1', saldo_inicial = 1200)
        accout = create_account(nombre='Account2', saldo_inicial = 800)
        mov = create_movement(cuenta_in = accin, cuenta_out = accout, monto=100)
        self.assertEqual(accout.balance, 700)
    
    def test_balance_agaisnt_previous_balance_input_movement(self):
        ''' Cuando se ingresa un movimiento de entrada, antes de cambiar el saldo 
            debe almacenarse como saldo anterior'''
        acc = create_account(nombre='Account', saldo_inicial = 1400)
        saldo = acc.balance
        mov = create_movement(cuenta_in = acc, monto = 100)
        self.assertEqual(acc.balance_previous, saldo)

    def test_balance_agaisnt_previous_balance_output_movement(self):
        ''' Cuando se ingresa un movimiento de salida, antes de cambiar el saldo 
            debe almacenarse como saldo anterior'''
        acc = create_account(nombre='Account', saldo_inicial = 1400)
        saldo = acc.balance
        mov = create_movement(cuenta_out = acc, monto = 100)
        self.assertEqual(acc.balance_previous, saldo)

    def test_balance_agaisnt_previous_balance_transfer_movement_account_in(self):
        ''' Cuando se ingresa un movimiento de traspaso, antes de cambiar el saldo 
            de la cuenta de entrada, debe almacenarse como saldo anterior'''
        accin = create_account(nombre='Account1', saldo_inicial = 1400)
        accout = create_account(nombre='Account2', saldo_inicial = 1900)
        saldo = accin.balance
        mov = create_movement(cuenta_in = accin, cuenta_out = accout, monto = 100)
        self.assertEqual(accin.balance_previous, saldo)

    def test_balance_agaisnt_previous_balance_transfer_movement_account_out(self):
        ''' Cuando se ingresa un movimiento de traspaso, antes de cambiar el saldo 
            de la cuenta de salida, debe almacenarse como saldo anterior'''
        accin = create_account(nombre='Account1', saldo_inicial = 1400)
        accout = create_account(nombre='Account2', saldo_inicial = 1900)
        saldo = accout.balance
        mov = create_movement(cuenta_in = accin, cuenta_out = accout, monto = 100)
        self.assertEqual(accout.balance_previous, saldo)

    def test_balance_against_initial_balance(self):
        ''' Comprueba que el saldo final de cada cuenta coincide con el saldo 
            inicial al que se le han aplicado los movimientos
        '''
        accin = create_account(nombre='Account1', saldo_inicial = 1400)
        accout = create_account(nombre='Account2', saldo_inicial = 1900)
        mov1 = create_movement(cuenta_in = accin, monto = 220)
        mov2 = create_movement(cuenta_out = accin, monto = 500)
        mov3 = create_movement(cuenta_in = accin, cuenta_out = accout, monto = 700)
        saldo = accin.balance
        
        for mov in accin.movements_in.all():
            saldo = saldo - mov.amount
        for mov in accin.movements_out.all():
            saldo = saldo + mov.amount
        
        self.assertEqual(accin.balance_start, saldo)
    
    def test_balance_against_initial_balance_random_values(self):
        ''' Comprueba que el saldo final de cada cuenta coincide con el saldo 
            inicial al que se le han aplicado movimientos con valores al azar
        '''
        
        TWOPLACES = decimal.Decimal(10) ** -2
        
        accin = create_account(nombre='Account1', saldo_inicial = 1400)
        accout = create_account(nombre='Account2', saldo_inicial = 1900)
        
        direction = int(random.uniform(0,3))
        for x in range(100):
            montorandom = decimal.Decimal(random.uniform(0,99999)).\
                                quantize(TWOPLACES)
            if direction == 0:
                mov = create_movement(cuenta_in = accin, monto = montorandom)
            elif direction == 1:
                mov = create_movement(cuenta_out = accin, monto = montorandom)
            else:
                mov = create_movement(cuenta_in = accin, cuenta_out = accout, 
                                      monto = montorandom)
                
        saldo = accin.balance            
        
        for mov in accin.movements_in.all():
            saldo = saldo - mov.amount
        for mov in accin.movements_out.all():
            saldo = saldo + mov.amount
        
        self.assertEqual(accin.balance_start, saldo)
