""" A lo largo de los comentarios de este archivo, se usa la siguiente nomenclatura:

        movimiento de salida: Objeto Movement que tiene un valor en el campo 
                              account_out y ninguno en el campo account_in
        movimiento de entrada: Objeto Movement que tiene un valor en el campo 
                               account_in y ninguno en el campo account_out
        movimiento de traspaso: Objeto Movement que tiene un valor en ambos campos, 
                                account_in y account_out
"""

import decimal
import random

from django.db.models import Sum
from django.test import TestCase
from django.utils import timezone

from finper.models import Account, Movement, Category


def create_account(cod, nombre, saldo_inicial):
    return Account.objects.create(
        codename=cod,
        name=nombre, 
        balance_start=saldo_inicial)


def create_category():
    return Category.objects.create(name='test', description='para pruebas')


def create_movement(cuenta_in=None, cuenta_out=None, monto=0):
    fecha = timezone.now()
    concepto = 'Movimiento de prueba'
    categoria = create_category()
    return Movement.objects.create(date=fecha,
                                   title=concepto,
                                   amount=monto,
                                   account_in=cuenta_in,
                                   account_out=cuenta_out,
                                   category=categoria)


class MovementModelTest(TestCase):
    """ Pruebas para el modelo Movement"""

    def test_mov_salida_resta_de_cuenta_de_salida(self):
        """ Acción:     Se crea un movimiento de salida
            Chequear:   El monto del movimiento debe restarse del saldo de
                        la cuenta de salida"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=5000)
        saldo = acc.balance
        mov = create_movement(cuenta_out=acc,
                              monto=500)
        self.assertEqual(saldo, mov.account_out.balance + mov.amount)

    def test_mov_entrada_suma_a_cuenta_de_entrada(self):
        """ Acción:     Se crea un movimiento de entrada
            Chequear:   El monto del movimiento debe sumarse al saldo de
                        la cuenta de entrada"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=1200)
        saldo = acc.balance
        mov = create_movement(cuenta_in=acc,
                              monto=600)
        self.assertEqual(saldo, mov.account_in.balance - mov.amount)

    def test_mov_trans_suma_a_cta_entrada_y_resta_de_cta_salida(self):
        """ Acción:     Se crea un movimiento de traspaso
            Chequear:   El monto del movimiento debe restarse del saldo de
                        la cuenta de salida y sumarse al saldo de la cuenta 
                        de entrada"""
        accin = create_account(cod='ai', nombre='Cuenta1', saldo_inicial=2000)
        accout = create_account(cod='ao', nombre='Cuenta2', saldo_inicial=4500)
        balin = accin.balance
        balout = accout.balance
        mov = create_movement(cuenta_in=accin,
                              cuenta_out=accout,
                              monto=900)
        self.assertEqual((balin, balout),
                         (mov.account_in.balance - mov.amount,
                          mov.account_out.balance + mov.amount)
                         )

    def test_en_mov_entrada_cuenta_de_salida_es_None(self):
        """ Acción:     Se crea un movimiento de entrada
            Chequear:   No se genera ningún contenido en la cuenta de salida del
                        movimiento"""
        accin = create_account(cod='act', nombre='Cuenta', saldo_inicial=4500)
        mov = create_movement(cuenta_in=accin, monto=800)
        self.assertIsNone(mov.account_out)

    def test_en_mov_salida_cuenta_de_entrada_es_None(self):
        """ Acción:     Se crea un movimiento de salida
            Chequear:   No se genera ningún contenido en la cuenta de entrada del
                        movimiento"""
        accout = create_account(cod='act', nombre='Cuenta', saldo_inicial=4500)
        mov = create_movement(cuenta_out=accout, monto=800)
        self.assertIsNone(mov.account_in)

    #     def test_trans_mov_account_in_and_out_must_be_different(self):
    #         """ Acción:     Se crea un movimiento de traspaso
    #             Chequear:   La cuenta de entrada y la de salida no son la misma cuenta"""
    #         accin = accout = create_account(cod='act', nombre='Cuenta1', saldo_inicial = 2000)
    #         ####accout = create_account(cod='act', nombre='Cuenta2', saldo_inicial = 4500)
    #         mov = create_movement(cuenta_in = accin, cuenta_out = accout,
    #                               monto = 900)
    #         self.assertNotEqual(mov.account_in, mov.account_out)

    def test_mov_tiene_al_menos_una_cuenta_asociada(self):
        """ Acción:     Se crea un movimiento de entrada
            Chequear:   Al menos una de las dos cuentas (la de entrada o la de salida)
                        tiene algún contenido"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=1200)
        mov = create_movement(cuenta_in=acc, monto=100)
        self.assertTrue(mov.account_in is not None or mov.account_out is not None)

    def test_mod_en_mov_trans_resta_el_monto_anterior_y_suma_el_nuevo_a_cta_de_entrada(self):
        """ Acción:     Se modifica el monto de un movimiento de traspaso
            Chequear:   El nuevo saldo de la cuenta de entrada es igual al 
                        saldo anterior a la modificación menos el monto anterior
                        del movimiento más el monto nuevo"""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=23400)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=34200)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=1500)
        balance = accin.balance
        mov.amount = 2000
        mov.save()
        self.assertEqual(mov.account_in.balance, balance - 1500 + 2000)

    def test_mod_en_mov_trans_suma_monto_anterior_y_resta_nuevo_de_cta_de_salida(self):
        """ Acción:     Se modifica el monto de un movimiento de traspaso
            Chequear:   El nuevo saldo de la cuenta de salida es igual al 
                        saldo anterior a la modificación más el monto anterior
                        del movimiento menos el monto nuevo"""
        accin = create_account(cod='ain', nombre='Account_in', saldo_inicial=23400)
        accout = create_account(cod='aou', nombre='Account_out', saldo_inicial=34200)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=1500)
        balance = accout.balance
        mov.amount = 2000
        mov.save()
        self.assertEqual(mov.account_out.balance, balance + 1500 - 2000)

    def test_mod_en_mov_entrada_resta_monto_anterior_y_suma_nuevo_a_cta_de_entrada(self):
        """ Acción:     Se modifica el monto de un movimiento de entrada
            Chequear:   El nuevo saldo de la cuenta de entrada es igual al 
                        saldo anterior a la modificación menos el monto anterior
                        del movimiento más el monto nuevo"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=23400)
        mov = create_movement(cuenta_in=acc, monto=1500)
        balance = acc.balance
        mov.amount = 2000
        mov.save()
        self.assertEqual(mov.account_in.balance, balance - 1500 + 2000)

    def test_mod_en_mov_salida_suma_monto_anterior_y_resta_nuevo_de_cta_de_salida(self):
        """ Acción:     Se modifica el monto de un movimiento de salida
            Chequear:   El nuevo saldo de la cuenta de salida es igual al 
                        saldo anterior a la modificación más el monto anterior
                        del movimiento menos el monto nuevo"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=23400)
        mov = create_movement(cuenta_out=acc, monto=1500)
        balance = acc.balance
        mov.amount = 2000
        mov.save()
        self.assertEqual(mov.account_out.balance, balance + 1500 - 2000)

    def test_si_mov_de_entrada_cambia_a_salida_con_otra_cuenta_resta_de_cta_entrada_anterior(self):
        """ Accion:    Un movimiento que tiene account_in y no account_out
                       pasa a tener account_out y no account_in
            Chequear:  movement.amount se resta del saldo de la vieja account_in"""
        accinold = create_account(cod='aio', nombre='Account_in_old', saldo_inicial=23400)
        accoutnew = create_account(cod='aon', nombre='Account_out_new', saldo_inicial=44580)
        mov = create_movement(cuenta_in=accinold, monto=1500)

        balance = accinold.balance

        mov.account_in = None
        mov.account_out = accoutnew
        mov.save()

        accinold = accinold.reconnect()

        self.assertEqual(accinold.balance, balance - 1500)

    def test_si_mov_entrada_cambia_a_salida_con_otra_cuenta_resta_de_cta_salida_nueva(self):
        """ Accion:    Un movimiento que tiene account_in y no account_out
                       pasa a tener account_out y no account_in
            Chequear:  movement.amount resta del saldo de la nueva account_out"""
        accinold = create_account(cod='aio', nombre='Account_in_old', saldo_inicial=23400)
        accoutnew = create_account(cod='aon', nombre='Account_out_new', saldo_inicial=44580)
        mov = create_movement(cuenta_in=accinold, monto=1500)
        balance = accoutnew.balance
        mov.account_in = None
        mov.account_out = accoutnew
        mov.save()
        self.assertEqual(accoutnew.balance, balance - 1500)

    def test_si_mov_entrada_cambia_a_salida_con_la_misma_cuenta_se_resta_dos_veces_de_la_cuenta(self):
        """ Accion:    Un movimiento que tiene account_in y no account_out
                       pasa a tener em account_out la cuenta que tenía en account_in
            Chequear:  movement.amount resta del saldo de la nueva account_out"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=23500)
        mov = create_movement(cuenta_in=acc, monto=1500)

        balance = acc.balance

        mov.account_out = mov.account_in
        mov.account_in = None
        mov.save()

        self.assertEqual(acc.reconnect().balance, balance - (1500 * 2))

    def test_si_mov_salida_cambia_a_entrada_con_cuentas_distintas_suma_a_cta_salida_anterior(self):
        """ Accion:    Un movimiento que tiene account_out y no account_in
                       pasa a tener account_in y no account_out
            Chequear:  movement.amount suma al saldo de la vieja account_out"""
        accoutold = create_account(cod='aoo', nombre='Account_in_old', saldo_inicial=23400)
        accinnew = create_account(cod='ain', nombre='Account_out_new', saldo_inicial=44580)
        mov = create_movement(cuenta_out=accoutold, monto=1500)

        balance = accoutold.balance

        mov.account_out = None
        mov.account_in = accinnew
        mov.save()

        self.assertEqual(accoutold.reconnect().balance, balance + 1500)

    def test_si_mov_salida_cambia_a_entrada_con_cuentas_distintas_suma_a_cta_entrda_nueva(self):
        """ Accion:    Un movimiento que tiene account_out y no account_in
                       pasa a tener account_in y no account_out
            Chequear:  movement.amount suma al saldo de la nueva account_in"""
        accoutold = create_account(cod='aoo', nombre='Account_in_old',
                                   saldo_inicial=20000)
        accinnew = create_account(cod='ain', nombre='Account_out_new',
                                  saldo_inicial=40000)
        mov = create_movement(cuenta_out=accoutold, monto=1500)

        balance = accinnew.balance

        mov.account_out = None
        mov.account_in = accinnew
        mov.save()

        self.assertEqual(accinnew.balance, balance + 1500)

    def test_si_mov_salida_cambia_a_entrada_con_la_misma_cuenta_se_sum_dos_veces_a_la_cuenta(self):
        """ Accion:    Un movimiento que tiene account_in y no account_out
                       pasa a tener en account_out la cuenta que tenía en account_in
            Chequear:  movement.amount resta del saldo de la nueva account_out"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=23500)
        mov = create_movement(cuenta_out=acc, monto=1500)

        balance = acc.balance
        mount = mov.amount

        mov.account_in = mov.account_out
        mov.account_out = None

        mov.save()

        self.assertEqual(acc.reconnect().balance, balance + (mov.amount * 2))

    def test_si_mov_trans_cambia_a_entrada_suma_a_cta_salida_anterior(self):
        """ Accion:    Un movimiento de traspaso pasa a ser de entrada
            Chequear:  Se suma el monto de la operación al saldo de la cuenta
                       de salida"""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=23488)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=34289)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=2340)

        balance = accout.balance

        mov.account_out = None
        mov.save()

        accout = accout.reconnect()

        self.assertEqual(accout.balance, balance + 2340)

    def test_si_mov_trans_cambia_a_entrada_saldo_cta_entrada_no_cambia(self):
        """ Accion:    Un movimiento de traspaso pasa a ser de entrada
            Chequear:  El saldo de la cuenta de entrada permanece igual"""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=23488)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=34289)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=2340)
        balance = accin.balance
        mov.account_out = None
        mov.save()
        self.assertEqual(accin.balance, balance)

    def test_si_mov_trans_cambia_a_salida_resta_de_cta_entrada_anterior(self):
        """ Accion:    Un movimiento de traspaso pasa a ser de salida
            Chequear   El monto del movimiento debe restarse de la vieja
                       cuenta de entrada."""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=23488)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=34289)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout,
                              monto=2340)

        balance = accin.balance

        mov.account_in = None
        mov.save()

        accin = accin.reconnect()

        self.assertEqual(accin.balance, balance - 2340)

    def test_si_mov_trans_cambia_a_salida_saldo_cta_salida_no_cambia(self):
        """ Accion:    Un movimiento de traspaso pasa a ser de salida
            Chequear:  El saldo de la cuenta de salida permanece igual"""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=23488)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=34289)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=2340)
        balance = accout.balance
        mov.account_in = None
        mov.save()
        self.assertEqual(accout.balance, balance)

    def test_si_mov_entrada_cambia_a_trans_resta_de_cta_salida(self):
        """ Accion:    Un movimiento de entrada pasa a ser de traspaso
            Chequear:  El monto del movimiento se resta del saldo de la cuenta
                       de salida"""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=23488)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=34289)
        mov = create_movement(cuenta_in=accin, monto=2350)
        mov.account_out = accout
        mov.save()
        self.assertEqual(accout.balance, 34289 - 2350)

    def test_si_mov_entrada_cambia_a_trans_saldo_cta_entrada_no_cambia(self):
        """ Accion:    Un movimiento de entrada pasa a ser de traspaso
            Chequear:  El saldo de la cuenta de entrada permanece igual"""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=23488)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=34289)
        mov = create_movement(cuenta_in=accin, monto=2350)
        balance = accin.balance
        mov.account_out = accout
        mov.save()
        self.assertEqual(accin.balance, balance)

    def test_si_mov_salida_cambia_a_trans_suma_a_cta_entrada(self):
        """ Accion:    Un movimiento de salida pasa a ser de traspaso
            Chequear:  El monto del movimiento se suma al saldo de la cuenta
                       de entrada"""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=23488)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=34289)
        mov = create_movement(cuenta_out=accout, monto=2350)
        mov.account_in = accin
        mov.save()
        self.assertEqual(accin.balance, 23488 + 2350)

    def test_si_mov_salida_cambia_a_trans_saldo_cta_salida_no_cambia(self):
        """ Accion:    Un movimiento de salida pasa a ser de traspaso
            Chequear:  El saldo de la cuenta de salida permanece igual"""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=23488)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=34289)
        mov = create_movement(cuenta_out=accout, monto=2350)
        balance = accout.balance
        mov.account_in = accin
        mov.save()
        self.assertEqual(accout.balance, balance)

    def test_si_en_mov_trans_cambian_de_lugar_ctas_entrada_y_salida_suma_2_veces_a_nueva_cta_entrada(self):
        """ Accion:    En un movimiento de traspaso, se intercambian la cuenta
                       de entrada y la de salida
            Chequear:  El monto del movimiento se suma dos veces al saldo de la 
                       nueva cuenta de entrada"""
        acc1 = create_account(cod='ac1', nombre='Account_1', saldo_inicial=23488)
        acc2 = create_account(cod='ac2', nombre='Account_2', saldo_inicial=34289)
        mov = create_movement(cuenta_in=acc1, cuenta_out=acc2, monto=2350)

        balance = mov.account_out.balance
        acc = mov.account_in

        mov.account_in = mov.account_out
        mov.account_out = acc
        mov.save()
        self.assertEqual(mov.account_in.balance, balance + (2 * 2350))

    def test_si_en_mov_trans_cambian_de_lugar_ctas_entrada_y_salida_resta_2_veces_de_nueva_cta_salida(self):
        """ Accion:    En un movimiento de traspaso, se intercambian la cuenta
                       de entrada y la de salida
            Chequear:  El monto del movimiento se suma dos veces al saldo de la 
                       nueva cuenta de entrada"""
        acc1 = create_account(cod='ac1', nombre='Account_1', saldo_inicial=23488)
        acc2 = create_account(cod='ac2', nombre='Account_2', saldo_inicial=34289)
        mov = create_movement(cuenta_in=acc1, cuenta_out=acc2, monto=2350)
        balance = mov.account_in.balance
        acc = mov.account_in
        mov.account_in = mov.account_out
        mov.account_out = acc
        mov.save()
        self.assertEqual(mov.account_out.balance, balance - (2 * 2350))

    def test_si_en_mov_entrada_cambia_cta_y_monto_resta_monto_anterior_de_cta_entrada_anterior(self):
        """ Acción:    En un movimiento de entrada, cambia la cuenta y se modifica
                       el monto.
            Chequear:  El viejo monto debe restarse del saldo de la vieja 
                       cuenta de entrada."""
        accold = create_account(cod='ao', nombre='Account_old', saldo_inicial=10000)
        accoldbal = accold.balance
        accnew = create_account(cod='an', nombre='Account_new', saldo_inicial=20000)
        mov = create_movement(cuenta_in=accold, monto=1000)

        mov.account_in = accnew
        mov.amount = 2000
        mov.save()

        # Volver a cargar accold desde la tabla (al ser reemplazada en mov
        # por accnew perdió la conexión.
        accold = Account.objects.get(pk=accold.id)

        self.assertEqual(accoldbal, accold.balance)

    def test_si_en_mov_entrada_cambia_cta_y_monto_suma_monto_nuevo_a_cta_entrada_nueva(self):
        """ Acción:    En un movimiento de entrada, cambia la cuenta y se
                       modifica
                       el monto.
            Chequear:  El nuevo monto debe sumarse al saldo de la nueva 
                       cuenta de entrada."""
        accold = create_account(cod='ao', nombre='Account_old', saldo_inicial=33000)

        accnew = create_account(cod='an', nombre='Account_new', saldo_inicial=84000)
        accnewbal = accnew.balance
        mov = create_movement(cuenta_in=accold, monto=500)

        mov.account_in = accnew

        mov.amount = 452
        mov.save()

        self.assertEqual(mov.account_in.balance, accnewbal + mov.amount)

    def test_si_en_mov_salida_cambia_cta_y_monto_suma_monto_anterior_a_cta_salida_anterior(self):
        """ Acción:    En un movimiento de salida, cambia la cuenta y se
                       modifica el monto.
            Chequear:  El viejo monto debe sumarse al saldo de la vieja 
                       cuenta de salida."""
        accold = create_account(cod='aol', nombre='Account_old', saldo_inicial=30000)
        accoldbal = accold.balance
        accnew = create_account(cod='anw', nombre='Account_new', saldo_inicial=100000)
        mov = create_movement(cuenta_out=accold, monto=500)

        mov.account_out = accnew
        mov.amount = 400
        mov.save()

        # Reconectar accold
        accold = Account.objects.get(pk=accold.pk)

        self.assertEqual(accold.balance, accoldbal)

    def test_si_en_mov_salida_cambia_cta_y_monto_resta_nuevo_monto_de_nueva_cta_salida(self):
        """ Acción:    En un movimiento de salida, cambia la cuenta y se modifica
                       el monto.
            Chequear:  El nuevo monto debe restarse al saldo de la nueva 
                       cuenta de salida."""
        accold = create_account(cod='aol', nombre='Account_old', saldo_inicial=30000)
        accnew = create_account(cod='anw', nombre='Account_new', saldo_inicial=50000)
        mov = create_movement(cuenta_out=accold, monto=500)

        balance = accnew.balance

        mov.account_out = accnew
        mov.amount = 400
        mov.save()
        self.assertEqual(accnew.balance, balance - mov.amount)

    def test_si_mov_entrada_cambia_a_salida_y_cambia_monto_resta_monto_anterior_y_nuevo_de_cta(self):
        """ Acción:    Un movimiento de entrada cambia a movimiento de salida
                       al mismo tiempo que se modifica el monto.
            Chequear:  Debe restarse el viejo monto sumado al nuevo monto del saldo 
                       de la cuenta."""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=10000)
        mov = create_movement(cuenta_in=acc, monto=200)

        balance = acc.balance
        mount = mov.amount

        mov.account_out = mov.account_in
        mov.account_in = None
        mov.amount = 400
        mov.save()
        self.assertEqual(mov.account_out.balance, balance - (mount + mov.amount))

    def test_si_mov_entrada_cambia_a_salida_y_cambia_cta_y_cambia_monto_resta_monto_anterior_de_cta_entrada_anterior(self):
        """ Acción:    Un movimiento de entrada cambia a movimiento de salida
                       con una cuenta diferente
                       al mismo tiempo que se modifica el monto.
            Chequear:  Debe restarse el viejo monto del saldo de la vieja cuenta
                       de entrada."""
        accinold = create_account(cod='aio', nombre='Account_in_old',
                                  saldo_inicial=10000)
        accinoldbalance = accinold.balance
        accoutnew = create_account(cod='aon', nombre='Account_out_new',
                                   saldo_inicial=50000)
        mov = create_movement(cuenta_in=accinold, monto=3000)

        mov.account_out = accoutnew
        mov.account_in = None
        mov.amount = 1500
        mov.save()

        # Al cambiar accinold por None en mov.account_in, ésta queda
        # desvinculada de mov. Por lo tanto, al salvarse mov, no se 
        # salva a accinold (si bien sí se modifica el saldo en la tabla 
        # de datos). Es por eso que es necesario volver a cargarla
        # desde la tabla antes de hacer la comparación.)
        accinold = Account.objects.get(pk=accinold.pk)

        self.assertEqual(accinoldbalance, accinold.balance)

    def test_si_mov_entrada_cambia_a_salida_y_cambia_cta_y_monto_resta_nuevo_monto_de_nueva_cuenta(self):
        """ Acción:    Un movimiento de entrada cambia a movimiento de salida
                       con una cuenta diferente
                       al mismo tiempo que se modifica el monto.
            Chequear:  Debe restarse el nuevo monto del saldo de la nueva cuenta
                       de salida."""
        accinold = create_account(cod='aio', nombre='Account_in_old', saldo_inicial=34698)
        accoutnew = create_account(cod='aon', nombre='Account_out_new', saldo_inicial=54335)
        mov = create_movement(cuenta_in=accinold, monto=3552)

        balance = accoutnew.balance

        mov.account_out = accoutnew
        mov.account_in = None
        mov.amount = 664
        mov.save()
        self.assertEqual(mov.account_out.balance, balance - mov.amount)

    def test_si_mov_salida_cambia_a_entrada_y_cambia_monto_suma_monto_anterior_y_nuevo_a_cta(self):
        """ Acción:    Un movimiento de salida cambia a movimiento de entrada
                       al mismo tiempo que se modifica el monto.
            Chequear:  Debe sumarse el viejo monto sumado al nuevo monto al saldo 
                       de la cuenta."""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=30000)
        mov = create_movement(cuenta_out=acc, monto=500)
        balance = acc.balance
        mount = mov.amount

        mov.account_in = mov.account_out
        mov.account_out = None
        mov.amount = 400
        mov.save()

        self.assertEqual(mov.account_in.balance, balance + (mount + mov.amount))

    def test_si_mov_salida_cambia_a_entrada_y_cambia_cta_y_monto_suma_monto_anterior_a_cta_anterior(self):
        """ Acción:    Un movimiento de salida cambia a movimiento de entrada
                       con una cuenta diferente
                       al mismo tiempo que se modifica el monto.
            Chequear:  Debe sumarse el viejo monto al saldo de la vieja cuenta
                       de salida."""
        accoutold = create_account(cod='aoo', nombre='Account_out_old', saldo_inicial=34698)
        accinnew = create_account(cod='ain', nombre='Account_in_new', saldo_inicial=54335)
        mov = create_movement(cuenta_out=accoutold, monto=3552)

        acc = mov.account_out
        balance = mov.account_out.balance
        mount = mov.amount

        mov.account_in = accinnew
        mov.account_out = None
        mov.amount = 664
        mov.save()

        acc = Account.objects.get(pk=acc.pk)

        self.assertEqual(acc.balance, balance + mount)

    def test_si_mov_salida_cambia_a_entrada_y_cambia_cta_y_monto_suma_nuevo_monto_a_nueva_cta_entrada(self):
        """ Acción:    Un movimiento de salida cambia a movimiento de entrada
                       con una cuenta diferente
                       al mismo tiempo que se modifica el monto.
            Chequear:  Debe sumarse el nuevo monto al saldo de la nueva cuenta
                       de entrada+."""
        accoutold = create_account(cod='aoo', nombre='Account_out_old', saldo_inicial=34698)
        accinnew = create_account(cod='ain', nombre='Account_in_new', saldo_inicial=54335)
        mov = create_movement(cuenta_out=accoutold, monto=3552)

        balance = accinnew.balance

        mov.account_in = accinnew
        mov.account_out = None
        mov.amount = 664
        mov.save()
        self.assertEqual(mov.account_in.balance, balance + mov.amount)

    def test_si_mov_entrada_cambia_a_trans_y_cambia_monto_resta_monto_anterior_y_suma_nuevo_a_cta_entrada(self):
        """ Acción:    Un movimiento de entrada cambia a movimiento de traspaso
                       al mismo tiempo que se modifica el monto.
            Chequear:  Debe restarse el viejo monto y sumarse el nuevo de la
                       cuenta de entrada."""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=54334)
        accoutnew = create_account(cod='aon', nombre='Account_out_new', saldo_inicial=144332)
        mov = create_movement(cuenta_in=accin, monto=2322)

        mount = mov.amount
        balance = mov.account_in.balance

        mov.amount = 3344
        mov.account_out = accoutnew
        mov.save()

        self.assertEqual(mov.account_in.balance, balance - mount + mov.amount)

    def test_si_mov_entrada_cambia_a_trans_y_cambia_monto_resta_nuevo_monto_de_nueva_cta_salida(self):
        """ Acción:    Un movimiento de entrada cambia a movimiento de traspaso
                       al mismo tiempo que se modifica el monto.
            Chequear:  Debe restarse el nuevo monto de la nueva cuenta de salida."""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=54334)
        accoutnew = create_account(cod='aon', nombre='Account_out_new', saldo_inicial=144332)
        mov = create_movement(cuenta_in=accin, monto=2322)

        balance = accoutnew.balance

        mov.amount = 3344
        mov.account_out = accoutnew
        mov.save()

        self.assertEqual(mov.account_out.balance, balance - mov.amount)

    def test_si_mov_salida_cambia_a_trans_y_cambia_monto_suma_monto_anterior_y_resta_nuevo_de_cta_salida(self):
        """ Acción:    Un movimiento de salida cambia a movimiento de traspaso
                       al mismo tiempo que se modifica el monto.
            Chequear:  Debe sumarse el viejo monto y restarse el nuevo 
                       de la cuenta de salida."""
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=54334)
        accinnew = create_account(cod='ain', nombre='Account_in_new', saldo_inicial=144332)
        mov = create_movement(cuenta_out=accout, monto=2322)

        mount = mov.amount
        balance = mov.account_out.balance

        mov.amount = 3344
        mov.account_in = accinnew
        mov.save()

        self.assertEqual(mov.account_out.balance, balance + mount - mov.amount)

    def test_si_mov_salida_cambia_a_trans_y_cambia_monto_suma_nuevo_monto_a_nueva_cta_entrada(self):
        """ Acción:    Un movimiento de entrada cambia a movimiento de traspaso
                       al mismo tiempo que se modifica el monto.
            Chequear:  Debe sumarse el nuevo monto a la nueva cuenta de entrada."""
        accout = create_account(cod='ao', nombre='Account_out',
                                saldo_inicial=50000)
        accinnew = create_account(cod='ain', nombre='Account_in_new',
                                  saldo_inicial=100000)
        balance = accinnew.balance
        mov = create_movement(cuenta_out=accout, monto=2000)

        mov.amount = 3000
        mov.account_in = accinnew
        mov.save()

        self.assertEqual(mov.account_in.balance, balance + mov.amount)

    def test_si_mov_trans_cambia_a_entrada_y_cambia_monto_suma_monto_anterior_a_cta_salida_anterior(self):
        """ Acción:    Un movimiento de traspaso cambia a movimiento de entrada
                       al mismo tiempo que se modifica el monto.
            Chequear:  Debe sumarse el viejo monto a la cuenta de salida 
                       eliminada."""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=54334)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=144332)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout,
                              monto=2322)

        mount = mov.amount
        acc = mov.account_out
        balance = mov.account_out.balance

        mov.amount = 3344
        mov.account_out = None
        mov.save()

        acc = acc.reconnect()

        self.assertEqual(acc.balance, balance + mount)

    def test_si_mov_trans_cambia_a_entrada_y_cambia_monto_resta_monto_anterior_y_suma_nuevo_a_cta_entrada(self):
        """ Acción:    Un movimiento de traspaso cambia a movimiento de entrada
                       al mismo tiempo que se modifica el monto.
            Chequear:  Debe restarse el viejo monto y sumarse el nuevo 
                       a la cuenta de entrada."""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=54334)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=144332)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=2322)

        mount = mov.amount
        balance = mov.account_in.balance

        mov.amount = 3344
        mov.account_out = None
        mov.save()

        self.assertEqual(mov.account_in.balance, balance - mount + mov.amount)

    def test_si_mov_trans_cambia_a_salida_y_cambia_monto_resta_monto_anterior_de_cta_entrada_anterior(self):
        """ Acción:    Un movimiento de traspaso cambia a movimiento de salida
                       al mismo tiempo que se modifica el monto.
            Chequear:  Debe restarse el viejo monto a la cuenta de entrada eliminada."""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=54334)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=144332)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout,
                              monto=2322)

        mount = mov.amount
        acc = mov.account_in
        balance = mov.account_in.balance

        mov.amount = 3344
        mov.account_in = None
        mov.save()

        acc = acc.reconnect()

        self.assertEqual(acc.balance, balance - mount)

    def test_si_mov_trans_cambia_a_salida_y_cambia_monto_suma_monto_anterior_y_resta_nuevo_de_cta_salida(self):
        """ Acción:    Un movimiento de traspaso cambia a movimiento de salida
                       al mismo tiempo que se modifica el monto.
            Chequear:  Debe sumarse el viejo monto y restarse el nuevo 
                       a la cuenta de entrada."""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=54334)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=144332)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=2322)

        mount = mov.amount
        balance = mov.account_out.balance

        mov.amount = 3344
        mov.account_in = None
        mov.save()

        self.assertEqual(mov.account_out.balance, balance + mount - mov.amount)

    def test_si_mov_trans_intercambia_ctas_de_entrada_y_salida_y_cambia_monto_resta_monto_anterior_y_nuevo_de_nueva_cta_salida(self):
        """ Acción:    Un movimiento de traspaso intercambia sus cuentas
                       de salida y de entrada
                       al mismo tiempo que se modifica el monto.
            Chequear:  Deben restarse el viejo monto y el nuevo 
                       a la cuenta intercambiada a la salida."""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=54334)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=144332)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=2322)

        mount = mov.amount
        balance = mov.account_in.balance

        mov.amount = 329
        acc = mov.account_in
        mov.account_in = mov.account_out
        mov.account_out = acc
        mov.save()

        self.assertEqual(mov.account_out.balance, balance - mount - mov.amount)

    def test_si_mov_trans_intercambia_ctas_de_entrada_y_salida_y_cambia_monto_suma_monto_anerior_y_nuevo_a_nueva_cta_entrada(self):
        """ Acción:    Un movimiento de traspaso intercambia sus cuentas
                       de salida y de entrada
                       al mismo tiempo que se modifica el monto.
            Chequear:  Deben sumarse el viejo monto y el nuevo 
                       a la cuenta intercambiada a la entrada."""
        accin = create_account(cod='ai', nombre='Account_in',
                               saldo_inicial=50000)
        accout = create_account(cod='ao', nombre='Account_out',
                                saldo_inicial=40000)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout,
                              monto=2000)

        mount = mov.amount
        balance = mov.account_out.balance

        mov.amount = 1000
        acc = mov.account_in
        mov.account_in = mov.account_out
        mov.account_out = acc
        mov.save()

        self.assertEqual(mov.account_in.balance, balance + mount + mov.amount)

    def test_si_en_mov_trans_cambia_cta_entrada_y_monto_resta_monto_anterior_de_cta_entrada_anterior(self):
        """ Acción:    En un movimiento de traspaso cambia la cuenta de entrada
                       al mismo tiempo que se modifica el monto.
            Chequear:  Debe restarse el viejo monto de la vieja cuenta de entrada."""
        accinold = create_account(cod='aio', nombre='Account_in_old',
                                  saldo_inicial=50000)
        accout = create_account(cod='ao', nombre='Account_out',
                                saldo_inicial=140000)
        accinnew = create_account(cod='ain', nombre='Account_in_new',
                                  saldo_inicial=200000)
        mov = create_movement(cuenta_in=accinold, cuenta_out=accout,
                              monto=2000)

        mount = mov.amount
        acc = mov.account_in
        balance = mov.account_in.balance

        mov.amount = 500
        mov.account_in = accinnew
        mov.save()

        acc = Account.objects.get(pk=acc.pk)

        self.assertEqual(acc.balance, balance - mount)

    def test_si_en_mov_trans_cambia_cta_de_entrada_y_monto_suma_nuevo_monto_a_nueva_cta_entrada(self):
        """ Acción:    En un movimiento de traspaso cambia la cuenta de entrada
                       al mismo tiempo que se modifica el monto.
            Chequear:  Debe sumarse el nuevo monto a la nueva cuenta de entrada."""
        accinold = create_account(cod='aio', nombre='Account_in_old', saldo_inicial=54334)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=144332)
        accinnew = create_account(cod='ain', nombre='Account_in_new', saldo_inicial=22346)
        mov = create_movement(cuenta_in=accinold, cuenta_out=accout, monto=2322)

        balance = accinnew.balance

        mov.amount = 667
        mov.account_in = accinnew
        mov.save()

        self.assertEqual(mov.account_in.balance, balance + mov.amount)

    def test_si_en_mov_trans_cambia_cta_salida_y_monto_suma_monto_anterior_a_cta_salida_anterior(self):
        """ Acción:    En un movimiento de traspaso cambia la cuenta de salida
                       al mismo tiempo que se modifica el monto.
            Chequear:  Debe sumarse el viejo monto a la vieja cuenta de salida."""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=50000)
        accoutold = create_account(cod='aoo', nombre='Account_out_old',
                                   saldo_inicial=40000)
        accoutnew = create_account(cod='aon', nombre='Account_out_new',
                                   saldo_inicial=20000)
        mov = create_movement(cuenta_in=accin, cuenta_out=accoutold,
                              monto=2000)

        mount = mov.amount
        acc = mov.account_out
        balance = mov.account_out.balance

        mov.amount = 1000
        mov.account_out = accoutnew
        mov.save()

        acc = acc.reconnect()

        self.assertEqual(acc.balance, balance + mount)

    def test_si_en_mov_trans_cambia_cta_salida_y_monto_resta_nuevo_monto_de_nueva_cta_salida(self):
        """ Acción:    En un movimiento de traspaso cambia la cuenta de salida
                       al mismo tiempo que se modifica el monto.
            Chequear:  Debe restarse el nuevo monto de la nueva cuenta de salida."""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=54334)
        accoutold = create_account(cod='aoo', nombre='Account_out_old', saldo_inicial=144332)
        accoutnew = create_account(cod='aon', nombre='Account_out_new', saldo_inicial=22346)
        mov = create_movement(cuenta_in=accin, cuenta_out=accoutold, monto=2322)

        balance = accoutnew.balance

        mov.amount = 667
        mov.account_out = accoutnew
        mov.save()

        self.assertEqual(mov.account_out.balance, balance - mov.amount)

        pass

    def test_si_en_mov_trans_cambia_cta_entrada_y_salida_y_monto_resta_monto_anterior_de_cta_entrada_anterior(self):
        """ Acción:    En un movimiento de traspaso cambian la cuenta de salida
                       y la de entrada al mismo tiempo que se modifica el monto.
            Chequear:  Debe restarse el viejo monto de la vieja 
                       cuenta de entrada."""
        accinold = create_account(cod='aio', nombre='Account_in_old',
                                  saldo_inicial=50000)
        accoutold = create_account(cod='aoo', nombre='Account_out_old',
                                   saldo_inicial=40000)
        accinnew = create_account(cod='ain', nombre='Account_in_new',
                                  saldo_inicial=80000)
        accoutnew = create_account(cod='aon', nombre='Account_out_new',
                                   saldo_inicial=20000)

        balance = accinold.balance

        mov = create_movement(cuenta_in=accinold,
                              cuenta_out=accoutold,
                              monto=2000)

        mov.amount = 1000
        mov.account_in = accinnew
        mov.account_out = accoutnew
        mov.save()

        accinold = accinold.reconnect()

        self.assertEqual(balance, accinold.balance)

    def test_si_en_mov_trans_cambian_cta_entrada_y_salida_y_monto_suma_nuevo_monto_a_nueva_cta_entrada(self):
        """ Acción:    En un movimiento de traspaso cambian la cuenta de salida
                       y la de entrada al mismo tiempo que se modifica el monto.
            Chequear:  Debe sumarse el nuevo monto a la nueva cuenta de entrada."""
        accinold = create_account(cod='aio', nombre='Account_in_old',
                                  saldo_inicial=50000)
        accoutold = create_account(cod='aoo', nombre='Account_out_old',
                                   saldo_inicial=40000)
        accinnew = create_account(cod='ain', nombre='Account_in_new',
                                  saldo_inicial=80000)
        accoutnew = create_account(cod='aon', nombre='Account_out_new',
                                   saldo_inicial=20000)
        mov = create_movement(cuenta_in=accinold,
                              cuenta_out=accoutold,
                              monto=2000)

        balance = accinnew.balance

        mov.amount = 1000
        mov.account_in = accinnew
        mov.account_out = accoutnew
        mov.save()

        self.assertEqual(mov.account_in.balance, balance + mov.amount)

    def test_si_en_mov_trans_cambia_cta_entrada_y_salida_y_monto_suma_monto_anterior_a_cta_salida_anerior(self):
        """ Acción:    En un movimiento de traspaso cambian la cuenta de salida
                       y la de entrada al mismo tiempo que se modifica el monto.
            Chequear:  Debe sumarse el viejo monto a la vieja cuenta de salida."""
        accinold = create_account(cod='aio', nombre='Account_in_old',
                                  saldo_inicial=50000)
        accoutold = create_account(cod='aoo', nombre='Account_out_old',
                                   saldo_inicial=40000)
        accinnew = create_account(cod='ain', nombre='Account_in_new',
                                  saldo_inicial=80000)
        accoutnew = create_account(cod='aon', nombre='Account_out_new',
                                   saldo_inicial=20000)

        accoutoldbal = accoutold.balance

        mov = create_movement(cuenta_in=accinold,
                              cuenta_out=accoutold,
                              monto=2000)

        mov.amount = 1000
        mov.account_in = accinnew
        mov.account_out = accoutnew
        mov.save()

        accoutold = accoutold.reconnect()

        self.assertEqual(accoutoldbal, accoutold.balance)

    def test_si_en_mov_trans_cambia_cta_entrada_y_salida_y_monto_resta_nuevo_monto_de_nueva_cta_salida(self):
        """ Acción:    En un movimiento de traspaso cambian la cuenta de salida
                       y la de entrada al mismo tiempo que se modifica el monto.
            Chequear:  Debe restarse el nuevo monto de la nueva cuenta de salida."""
        accinold = create_account(cod='aio', nombre='Account_in_old',
                                  saldo_inicial=50000)
        accoutold = create_account(cod='aoo', nombre='Account_out_old',
                                   saldo_inicial=40000)
        accinnew = create_account(cod='ain', nombre='Account_in_new',
                                  saldo_inicial=80000)
        accoutnew = create_account(cod='aon', nombre='Account_out_new',
                                   saldo_inicial=20000)

        balance = accoutnew.balance

        mov = create_movement(cuenta_in=accinold,
                              cuenta_out=accoutold,
                              monto=2000)

        mov.amount = decimal.Decimal(1000)
        mov.account_in = accinnew
        mov.account_out = accoutnew
        mov.save()

        self.assertEqual(mov.account_out.balance, balance - mov.amount)

    def test_si_en_mov_trans_cambia_cta_entrada_y_esta_pasa_a_salida_suma_nuevo_monto_a_nueva_cta_entrada(self):
        """ Acción:    En un movimiento de traspaso la cuenta de entrada pasa a
                       ser la de salida y es reemplazada por una nueva cuenta
                       de entrada, al mismo tiempo que cambia el monto.
            Chequear:  Debe sumarse el nuevo monto a la nueva cuenta de entrada."""
        accinold = create_account(cod='aio', nombre='Account_in_old',
                                  saldo_inicial=50000)
        accoutold = create_account(cod='aoo', nombre='Account_out_old',
                                   saldo_inicial=40000)
        accinnew = create_account(cod='ain', nombre='Account_in_new',
                                  saldo_inicial=80000)

        accinnewbal = accinnew.balance

        mov = create_movement(cuenta_in=accinold, cuenta_out=accoutold,
                              monto=2000)

        mov.amount = 1000
        mov.account_out = mov.account_in
        mov.account_in = accinnew
        mov.save()

        self.assertEqual(mov.account_in.balance, accinnewbal + mov.amount)

    def test_si_en_mov_trans_cambia_cta_entrada_y_esta_pasa_a_ser_salida_y_cambia_monto_resta_monto_anterior_y_nuevo_a_cta_intercambiada_a_salida(self):
        """ Acción:    En un movimiento de traspaso la cuenta de entrada pasa a
                       ser la de salida y es reemplazada por una nueva cuenta
                       de entrada, al mismo tiempo que cambia el monto.
            Chequear:  Deben restarse el viejo y el nuevo monto a la 
                       cuenta que ahora es de salida."""
        accinold = create_account(cod='aio', nombre='Account_in_old',
                                  saldo_inicial=50000)
        accoutold = create_account(cod='aoo', nombre='Account_out_old',
                                   saldo_inicial=40000)
        accinnew = create_account(cod='ain', nombre='Account_in_new',
                                  saldo_inicial=80000)
        mov = create_movement(cuenta_in=accinold,
                              cuenta_out=accoutold,
                              monto=2000)

        mount = mov.amount
        balance = mov.account_in.balance

        mov.amount = 1000
        mov.account_out = mov.account_in
        mov.account_in = accinnew
        mov.save()

        self.assertEqual(mov.account_out.balance, balance - mount - mov.amount)

    def test_si_en_mov_trans_cambia_cta_salida_y_esta_pasa_a_entrada_y_cambia_monto_resta_nuevo_monto_de_nueva_cta_salida(self):
        """ Acción:    En un movimiento de traspaso la cuenta de salida pasa a
                       ser la de entrada y es reemplazada por una nueva cuenta
                       de salida, al mismo tiempo que cambia el monto.
            Chequear:  Debe restarse el nuevo monto de la nueva cuenta de salida."""
        accinold = create_account(cod='aio', nombre='Account_in_old', saldo_inicial=54334)
        accoutold = create_account(cod='aoo', nombre='Account_out_old', saldo_inicial=144332)
        accoutnew = create_account(cod='aon', nombre='Account_out_new', saldo_inicial=88608)
        mov = create_movement(cuenta_in=accinold,
                              cuenta_out=accoutold,
                              monto=2322)

        balance = accoutnew.balance

        mov.amount = decimal.Decimal('4432.23')
        mov.account_in = mov.account_out
        mov.account_out = accoutnew
        mov.save()

        self.assertEqual(mov.account_out.balance, balance - mov.amount)

    def test_si_en_mov_trans_cambia_cta_salida_y_esta_pasa_a_entrada_y_cambia_monto_suma_viejo_y_nuevo_monto_a_cta_intercambiada_a_entrada(self):
        """ Acción:    En un movimiento de traspaso la cuenta de salida pasa a
                       ser la de entrada y es reemplazada por una nueva cuenta
                       de salida, al mismo tiempo que cambia el monto.
            Chequear:  Deben sumarse el viejo y el nuevo monto a la nueva 
                       cuenta de entrada."""
        accinold = create_account(cod='aio', nombre='Account_in_old',
                                  saldo_inicial=50000)
        accoutold = create_account(cod='aoo', nombre='Account_out_old',
                                   saldo_inicial=40000)
        accoutnew = create_account(cod='aon', nombre='Account_out_new',
                                   saldo_inicial=80000)
        mov = create_movement(cuenta_in=accinold,
                              cuenta_out=accoutold,
                              monto=2000)

        mount = mov.amount
        balance = mov.account_out.balance

        mov.amount = 1000
        mov.account_in = mov.account_out
        mov.account_out = accoutnew
        mov.save()

        self.assertEqual(mov.account_in.balance, balance + mount + mov.amount)
        pass


#     def test_mov_has_at_least_one_acc(self):
#         """ Acción:     Se crea un movimiento sin especificar cuenta.
#             Chequear:   Debería elevarse una excepción"""
#         c = create_category()
#         mov = Movement(date = datetime.date(2020,3,10), 
#                           title='Movimiento nuevo', 
#                           amount = 2000, 
#                           category = c)
#         try:
#             mov.save()
#         except: 
#             if mov.account_in == None:
#                 self.assertIsNotNone(mov.account_out)
#             self.assertIsNotNone(mov.account_in)


class AccountModelTest(TestCase):
    """ Pruebas para el modelo Account"""

    def test_cuenta_nueva_saldo_final_igual_a_inicial(self):
        """ Acción:     Se crea una cuenta nueva
            Chequear:   El saldo de la cuenta debe ser igual al saldo inicial"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=1200)
        self.assertEqual(acc.balance_start, acc.balance)

    def test_cuenta_nueva_saldo_previo_igual_a_cero(self):
        """ Acción:     Se crea una cuenta nueva
            Chequear:   El saldo previo de la cuenta debe ser igual a cero"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=1200)
        self.assertEqual(acc.balance_previous, 0)

    def test_salvar_cuenta_existente_no_iguala_saldo_al_inicial(self):
        """ Acción:     Se modifica una cuenta existente, con saldo distinto al
                        inicial
            Chequear:   El saldo de la cuenta debe seguir siendo distinto del 
                        saldo inicial"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=1200)
        create_movement(cuenta_in=acc, monto=500)
        acc.save()
        acc.name = 'Cuenta'
        acc.save()
        self.assertNotEqual(acc.balance_start, acc.balance)

    def test_salvar_cta_existente_no_igual_saldo_previo_a_cero(self):
        """ Acción:     Se modifica una cuenta existente, con saldo anterior
                        distinto de cero
            Chequear:   El saldo anterior de la cuenta debe seguir siendo 
                        distinto de cero"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=1200)
        mov = create_movement(cuenta_in=acc, monto=100)
        acc.name = 'Cuenta'
        acc.save()
        self.assertNotEqual(acc.balance_previous, 0)

    def test_mov_entrada_se_guarda_en_movements_in(self):
        """ Acción:     Se genera un movimiento de entrada en la cuenta
            Chequear:   El movimiento generado debe ir a movements_in en la cuenta"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=1200)
        mov = create_movement(cuenta_in=acc, monto=100)
        self.assertIs(acc.movements_in.count(), 1)

    def test_mov_entrada_no_se_guarda_en_movements_out(self):
        """ Acción:     Se genera un movimiento de entrada en la cuenta
            Chequear:   El movimiento generado no debe ir a movements_out en la 
                        cuenta"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=1200)
        mov = create_movement(cuenta_in=acc, monto=100)
        self.assertIs(acc.movements_out.count(), 0)

    def test_mov_salida_se_guarda_en_movements_out(self):
        """ Acción:     Se genera un movimiento de salida en la cuenta
            Chequear:   El movimiento generado debe ir a movements_out en la cuenta"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=1200)
        mov = create_movement(cuenta_out=acc, monto=100)
        self.assertIs(acc.movements_out.count(), 1)

    def test_mov_salida_no_se_guarda_en_movements_in(self):
        """ Acción:     Se genera un movimiento de salida en la cuenta
            Chequear:   El movimiento generado no debe ir a movements_in en la 
                        cuenta"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=1200)
        mov = create_movement(cuenta_out=acc, monto=100)
        self.assertIs(acc.movements_in.count(), 0)

    def test_mov_trans_se_guarda_en_movements_in_de_cta_entrada(self):
        """ Acción:     Se genera un movimiento de traspaso
            Chequear:   El movimiento generado debe ir a movements_in en la cuenta
                        de entrada"""
        accin = create_account(cod='ai', nombre='Account1', saldo_inicial=1200)
        accout = create_account(cod='ao', nombre='Account2', saldo_inicial=800)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=100)
        self.assertIs(accin.movements_in.count(), 1)

    def test_mov_trans_no_se_guarda_en_movements_out_en_cta_entrada(self):
        """ Acción:     Se genera un movimiento de traspaso
            Chequear:   El movimiento generado no debe ir a movements_out en la cuenta
                        de entrada"""
        accin = create_account(cod='ai', nombre='Account1', saldo_inicial=1200)
        accout = create_account(cod='ao', nombre='Account2', saldo_inicial=800)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=100)
        self.assertIs(accin.movements_out.count(), 0)

    def test_mov_trans_se_guarda_en_movements_out_en_cta_salida(self):
        """ Acción:     Se genera un movimiento de traspaso
            Chequear:   El movimiento generado debe ir a movements_out en la cuenta
                        de salida"""
        accin = create_account(cod='ai', nombre='Account1', saldo_inicial=1200)
        accout = create_account(cod='ao', nombre='Account2', saldo_inicial=800)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=100)
        self.assertIs(accout.movements_out.count(), 1)

    def test_mov_trans_no_se_guarda_en_movements_in_en_cta_salida(self):
        """ Acción:     Se genera un movimiento de traspaso
            Chequear:   El movimiento generado no debe ir a movements_in en la cuenta
                        de salida"""
        accin = create_account(cod='ai', nombre='Account1', saldo_inicial=1200)
        accout = create_account(cod='ao', nombre='Account2', saldo_inicial=800)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=100)
        self.assertIs(accout.movements_in.count(), 0)

    def test_mov_entrada_suma_al_saldo(self):
        """ Acción:     Se genera un movimiento de entrada
            Chequear:   El movimiento generado debe sumarse al saldo de la cuenta
                        de entrada"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=1200)
        mov = create_movement(cuenta_in=acc, monto=100)
        self.assertEqual(acc.balance, 1300)

    def test_mov_salida_resta_del_saldo(self):
        """ Acción:     Se genera un movimiento de salida
            Chequear:   El movimiento generado debe restarse del saldo de la cuenta
                        de salida"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=1200)
        mov = create_movement(cuenta_out=acc, monto=100)
        self.assertEqual(acc.balance, 1100)

    def test_mov_trans_suma_al_saldo_de_cta_entrada(self):
        """ Acción:     Se genera un movimiento de traspaso
            Chequear:   El movimiento generado debe sumarse al saldo de la cuenta
                        de entrada"""
        accin = create_account(cod='ai', nombre='Account1', saldo_inicial=1200)
        accout = create_account(cod='ao', nombre='Account2', saldo_inicial=800)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=100)
        self.assertEqual(accin.balance, 1300)

    def test_mov_trans_resta_del_saldo_de_cta_salida(self):
        """ Acción:     Se genera un movimiento de traspaso
            Chequear:   El movimiento generado debe restarse del saldo de la cuenta
                        de salida"""
        accin = create_account(cod='ai', nombre='Account1', saldo_inicial=1200)
        accout = create_account(cod='ao', nombre='Account2', saldo_inicial=800)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=100)
        self.assertEqual(accout.balance, 700)

    def test_mov_entrada_guarda_saldo_en_saldo_previo(self):
        """ Acción:     Se genera un movimiento de entrada
            Chequear:   El saldo de la cuenta de entrada debe almacenarse en el
                        saldo previo"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=1400)
        saldo = acc.balance
        mov = create_movement(cuenta_in=acc, monto=100)
        self.assertEqual(acc.balance_previous, saldo)

    def test_mov_salida_guarda_saldo_en_saldo_previo(self):
        """ Acción:     Se genera un movimiento de salida
            Chequear:   El saldo de la cuenta de salida debe almacenarse en el
                        saldo previo"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=1400)
        saldo = acc.balance
        mov = create_movement(cuenta_out=acc, monto=100)
        self.assertEqual(acc.balance_previous, saldo)

    def test_mov_trans_guarda_saldo_en_saldo_previo_en_cta_entrada(self):
        """ Acción:     Se genera un movimiento de traspaso
            Chequear:   El saldo de la cuenta de entrada debe almacenarse en el
                        saldo previo"""
        accin = create_account(cod='ai', nombre='Account1', saldo_inicial=1400)
        accout = create_account(cod='ao', nombre='Account2', saldo_inicial=1900)
        saldo = accin.balance
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=100)
        self.assertEqual(accin.balance_previous, saldo)

    def test_mov_trans_guarda_saldo_en_saldo_previo_en_cta_salida(self):
        """ Acción:     Se genera un movimiento de traspaso
            Chequear:   El saldo de la cuenta de salida debe almacenarse en el
                        saldo previo"""
        accin = create_account(cod='ai', nombre='Account1', saldo_inicial=1400)
        accout = create_account(cod='ao', nombre='Account2', saldo_inicial=1900)
        saldo = accout.balance
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=100)
        self.assertEqual(accout.balance_previous, saldo)

    def test_si_se_borra_un_mov_de_entrada_desaparece_de_movements_in(self):
        """ Acción:     Se elimina un movimiento de entrada relacionado con
                        una cuenta 
            Chequear:   El movimiento eliminado debe retirarse de la lista
                        movements_in de la cuenta"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=23400)
        mov = create_movement(cuenta_in=acc, monto=1500)
        mov.delete()
        self.assertNotIn(mov, acc.movements_in.all())

    def test_si_se_borra_un_mov_de_salida_desaparece_de_movements_out(self):
        """ Acción:     Se elimina un movimiento de salida relacionado con 
                        una cuenta 
            Chequear:   El movimiento eliminado debe retirarse de la lista
                        movements_out de la cuenta"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=23400)
        mov = create_movement(cuenta_out=acc, monto=1500)
        mov.delete()
        self.assertNotIn(mov, acc.movements_out.all())

    def test_si_se_borra_un_mov_de_entrada_se_resta_del_saldo(self):
        """ Acción:     Se elimina un movimiento de entrada relacionado con
                        una cuenta 
            Chequear:   El monto del movimiento eliminado debe restarse del saldo 
                        de la cuenta"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=23400)
        mov = create_movement(cuenta_in=acc, monto=1500)
        mov.delete()
        self.assertEqual(acc.balance, 23400)

    def test_si_se_borra_un_mov_de_salida_se_suma_al_saldo(self):
        """ Acción:     Se elimina un movimiento de salida relacionado con
                        una cuenta 
            Chequear:   El monto del movimiento eliminado debe sumarse al saldo 
                        de la cuenta"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=23400)
        mov = create_movement(cuenta_out=acc, monto=1500)
        mov.delete()
        self.assertEqual(acc.balance, 23400)

    def test_si_se_borra_un_mov_trans_se_resta_del_saldo_de_cta_entrada(self):
        """ Acción:     Se elimina un movimiento de traspaso del cual la cuenta es
                        cuenta de entrada
            Chequear:   El movimiento eliminado debe restarse del saldo 
                        de la cuenta"""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=25500)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=34200)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=2300)
        mov.delete()
        self.assertEqual(accin.balance, 25500)

    def test_si_se_borra_un_mov_trans_se_suma_al_saldo_de_cta_salida(self):
        """ Acción:     Se elimina un movimiento de traspaso del cual la cuenta es
                        cuenta de entrada
            Chequear:   El movimiento eliminado debe sumarse al saldo 
                        de la cuenta"""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=25500)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=34200)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=2300)
        mov.delete()
        self.assertEqual(accout.balance, 34200)

    def test_si_se_modifica_saldo_de_mov_salida_se_suma_saldo_anterior_y_se_resta_el_nuevo_del_saldo(self):
        """ Acción:     Se modifica el monto de un movimiento de salida relacionado
                        con la cuenta.
            Chequear:   El nuevo saldo de la cuenta es igual al 
                        saldo anterior a la modificación 
                        más el monto anterior del movimiento 
                        menos el monto nuevo"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=23400)
        mov = create_movement(cuenta_out=acc, monto=1500)
        balance = acc.balance
        mov.amount = 2000
        mov.save()
        self.assertEqual(acc.balance, balance + 1500 - 2000)

    def test_si_se_modifica_saldo_de_mov_entrada_se_resta_saldo_anterior_y_se_suma_el_nuevo_al_saldo(self):
        """ Acción:     Se modifica el monto de un movimiento de entrada
                        relacionado con la cuenta.
            Chequear:   El nuevo saldo de la cuenta es igual al 
                        saldo anterior a la modificación 
                        menos el monto anterior del movimiento 
                        más el monto nuevo"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=23400)
        mov = create_movement(cuenta_in=acc, monto=1500)

        balance = acc.balance
        mount = mov.amount

        mov.amount = 2000
        mov.save()

        self.assertEqual(acc.balance, balance - mount + mov.amount)

    def test_si_se_modifica_saldo_de_mov_trans_se_resta_saldo_anterior_y_se_suma_el_nuevo_al_saldo_de_cta_entrada(self):
        """ Acción:     Se modifica el monto de un movimiento de traspaso del cual
                        la cuenta es cuenta de entrada
            Chequear:   El nuevo saldo de la cuenta es igual al 
                        saldo anterior a la modificación 
                        menos el monto anterior del movimiento 
                        más el monto nuevo"""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=23400)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=34500)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=1500)
        balance = accin.balance
        mov.amount = 2000
        mov.save()
        self.assertEqual(accin.balance, balance - 1500 + 2000)

    def test_si_se_modifica_saldo_de_mov_trans_se_suma_el_monto_anterior_y_se_resta_el_nuevo_del_saldo_de_cta_salida(self):
        """ Acción:     Se modifica el monto de un movimiento de traspaso del cual
                        la cuenta es cuenta de salida
            Chequear:   El nuevo saldo de la cuenta es igual al 
                        saldo anterior a la modificación 
                        más el monto anterior del movimiento 
                        menos el monto nuevo"""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=23400)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=34500)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=1500)
        balance = accout.balance
        mov.amount = 2000
        mov.save()
        self.assertEqual(accout.balance, balance + 1500 - 2000)

    def test_si_cambia_cta_entrada_en_mov_se_resta_del_saldo_de_cta_anterior(self):
        """ Acción:     En un movimiento de entrada se cambia la cuenta de entrada
            Chequear:   Monto del movimiento se resta del saldo de la vieja cuenta 
                        de entrada"""
        accold = create_account(cod='ao', nombre='Account_in', saldo_inicial=25500)
        balorig = accold.balance
        accnew = create_account(cod='an', nombre='Account_new_in', saldo_inicial=34200)
        mov = create_movement(cuenta_in=accold, monto=1500)
        balance = mov.account_in.balance
        mount = mov.amount

        mov.account_in = accnew
        mov.save()

        self.assertEqual(balorig, balance - mount)

    def test_si_cambia_cta_entrada_en_mov_se_suma_al_saldo_de_nueva_cta(self):
        """ Acción:   En un movimiento de entrada se cambia la cuenta de entrada
            Chequear:   Monto del movimiento se suma al saldo de la nueva cuenta 
                        de entrada"""
        accold = create_account(cod='ao', nombre='Account_in', saldo_inicial=25500)
        accnew = create_account(cod='an', nombre='Account_new_in',
                                saldo_inicial=34200)
        mov = create_movement(cuenta_in=accold, monto=1500)
        mov.account_in = accnew
        mov.save()
        self.assertEqual(accnew.balance, 34200 + 1500)

    def test_si_cambia_cta_salida_en_mov_se_suma_al_saldo_de_cta_anterior(self):
        """ Acción:     En un movimiento de salida se cambia la cuenta de salida
            Chequear:   Monto del movimiento se suma al saldo de la vieja cuenta 
                        de salida"""
        accold = create_account(cod='ao', nombre='Account_out', saldo_inicial=25500)
        balorig = accold.balance
        accnew = create_account(cod='an', nombre='Account_new_out',
                                saldo_inicial=34200)
        mov = create_movement(cuenta_out=accold, monto=1500)

        balance = mov.account_out.balance
        mount = mov.amount

        mov.account_out = accnew
        mov.save()

        self.assertEqual(balorig, balance + mount)

    def test_si_cambia_cta_salida_en_mov_se_resta_del_saldo_de_nueva_cta(self):
        """ Acción:     En un movimiento de salida se cambia la cuenta de salida
            Chequear:   Monto del movimiento se resta del saldo de la nueva cuenta 
                        de salida"""
        accold = create_account(cod='ao', nombre='Account_out', saldo_inicial=25500)
        accnew = create_account(cod='an', nombre='Account_new_out',
                                saldo_inicial=34200)
        balorig = accnew.balance
        mov = create_movement(cuenta_out=accold, monto=1500)

        mov.account_out = accnew
        mov.save()

        self.assertEqual(accnew.balance, balorig - mov.amount)

    def test_si_cambia_la_cta_de_entrada_en_mov_trans_se_resta_del_saldo_de_cta_entrada_anterior(self):
        """ Acción:     En un movimiento de traspaso cambia la cuenta de entrada
            Chequear:   Monto del movimiento se resta del saldo de la vieja 
                        cuenta de entrada"""
        accinold = create_account(cod='aio', nombre='Account_in', saldo_inicial=25500)
        accinoldbal = accinold.balance
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=34200)
        accinnew = create_account(cod='ain', nombre='Account_another',
                                  saldo_inicial=50200)
        mov = create_movement(cuenta_in=accinold, cuenta_out=accout,
                              monto=2300)

        balance = accinold.balance

        mov.account_in = accinnew
        mov.save()
        self.assertEqual(accinoldbal, balance - mov.amount)

    def test_si_cambia_la_cta_de_entrada_en_mov_trans_se_suma_al_saldo_de_nueva_cta_entrada(self):
        """ Acción:     En un movimiento de traspaso cambia la cuenta de entrada
            Chequear:   Monto del movimiento se suma al saldo de la nueva cuenta 
                        de entrada"""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=25500)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=34200)
        accotra = create_account(cod='aot', nombre='Account_another', saldo_inicial=40200)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=2300)
        mov.account_in = accotra
        mov.save()
        self.assertEqual(accotra.balance, 40200 + 2300)

    def test_si_cambia_la_cta_de_salida_en_mov_trans_se_suma_al_saldo_de_cta_salida_anterior(self):
        """ Acción:     En un movimiento de traspaso cambia la cuenta de salida
            Chequear:   Monto del movimiento se suma al saldo de la vieja cuenta 
                        de salida"""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=25500)
        accoutold = create_account(cod='aoo', nombre='Account_out',
                                   saldo_inicial=34200)
        baloutold = accoutold.balance
        accoutnew = create_account(cod='aon', nombre='Account_out_new',
                                   saldo_inicial=50200)
        mov = create_movement(cuenta_in=accin, cuenta_out=accoutold,
                              monto=2300)

        balance = accoutold.balance

        mov.account_out = accoutnew
        mov.save()

        self.assertEqual(baloutold, balance + mov.amount)

    def test_si_cambia_la_cta_de_salida_en_mov_trans_se_resta_del_saldo_de_nueva_cta_salida(self):
        """ Acción:     En un movimiento de traspaso cambia la cuenta de salida
            Chequear:   Monto del movimiento se resta del saldo de la nueva cuenta 
                        de salida"""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=25500)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=34200)
        accotra = create_account(cod='aa', nombre='Account_another', saldo_inicial=50200)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=2300)
        mov.account_out = accotra
        mov.save()
        self.assertEqual(accotra.balance, 50200 - 2300)

    def test_si_cambia_la_cta_de_entrada_en_mov_se_elimina_el_mov_de_cta_entrada_anterior(self):
        """ Acción:    En un movimiento de entrada cambia la cuenta de entrada
            Chequear:  El movimiento debe eliminarse de movements_in en la vieja
                       cuenta de entrada"""
        accold = create_account(cod='ao', nombre='Account_old', saldo_inicial=34500)
        accnew = create_account(cod='an', nombre='Account_new', saldo_inicial=55880)
        mov = create_movement(cuenta_in=accold, monto=3450)
        mov.account_in = accnew
        mov.save()
        self.assertNotIn(mov, accold.movements_in.all())

    def test_si_cambia_la_cta_de_entrada_en_mov_se_agrega_el_mov_a_nueva_cta_entrada(self):
        """ Acción:    En un movimiento de entrada cambia la cuenta de entrada
            Chequear:  El movimiento debe agregarse a movements_in en la nueva
                       cuenta de entrada"""
        accold = create_account(cod='ao', nombre='Account_old', saldo_inicial=34500)
        accnew = create_account(cod='an', nombre='Account_new', saldo_inicial=55880)
        mov = create_movement(cuenta_in=accold, monto=3450)
        mov.account_in = accnew
        mov.save()
        self.assertIn(mov, accnew.movements_in.all())

    def test_si_cambia_la_cta_de_salida_en_mov_se_elimina_el_mov_de_cta_salida_anterior(self):
        """ Acción:    En un movimiento de salida cambia la cuenta de salida
            Chequear:  El movimiento debe eliminarse de movements_out en la vieja
                       cuenta de salida"""
        accold = create_account(cod='ao', nombre='Account_old', saldo_inicial=34500)
        accnew = create_account(cod='an', nombre='Account_new', saldo_inicial=55880)
        mov = create_movement(cuenta_out=accold, monto=3450)
        mov.account_out = accnew
        mov.save()
        self.assertNotIn(mov, accold.movements_out.all())

    def test_si_cambia_la_cta_de_salida_en_mov_se_agrega_el_mov_a_nueva_cta_salida(self):
        """ Acción:    En un movimiento de salida cambia la cuenta de salida
            Chequear:  El movimiento debe agregarse a movements_out en la nueva
                       cuenta de salida"""
        accold = create_account(cod='ao', nombre='Account_old', saldo_inicial=34500)
        accnew = create_account(cod='an', nombre='Account_new', saldo_inicial=55880)
        mov = create_movement(cuenta_out=accold, monto=3450)
        mov.account_out = accnew
        mov.save()
        self.assertIn(mov, accnew.movements_out.all())

    def test_si_cambia_la_cta_de_entrada_en_mov_trans_se_elimina_el_mov_de_cta_entrada_anterior(self):
        """ Acción:    En un movimiento de traspaso cambia la cuenta de entrada
            Chequear:  El movimiento debe eliminarse de movements_in en la vieja
                       cuenta de entrada"""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=25500)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=34200)
        accnew = create_account(cod='an', nombre='Account_another', saldo_inicial=50200)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=2300)
        mov.account_in = accnew
        mov.save()
        self.assertNotIn(mov, accin.movements_in.all())

    def test_si_cambia_la_cta_de_entrada_en_mov_trans_se_agrega_el_mov_a_nueva_cta_entrada(self):
        """ Acción:    En un movimiento de traspaso cambia la cuenta de entrada
            Chequear:  El movimiento debe agregarse a movements_in en la nueva
                       cuenta de entrada"""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=25500)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=34200)
        accnew = create_account(cod='an', nombre='Account_another', saldo_inicial=50200)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=2300)
        mov.account_in = accnew
        mov.save()
        self.assertIn(mov, accnew.movements_in.all())

    def test_si_cambia_la_cta_de_salida_en_mov_trans_se_elimina_el_mov_de_cta_salida_anterior(self):
        """ Acción:    En un movimiento de traspaso cambia la cuenta de salida
            Chequear:  El movimiento debe eliminarse de movements_out en la vieja
                       cuenta de salida"""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=25500)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=34200)
        accnew = create_account(cod='an', nombre='Account_another', saldo_inicial=50200)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=2300)
        mov.account_out = accnew
        mov.save()
        self.assertNotIn(mov, accout.movements_out.all())

    def test_si_cambia_la_cta_de_salida_en_mov_trans_se_agrega_el_mov_a_nueva_cta_salida(self):
        """ Acción:    En un movimiento de traspaso cambia la cuenta de salida
            Chequear:  El movimiento debe agregarse a movements_out en la nueva
                       cuenta de salida"""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=25500)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=34200)
        accnew = create_account(cod='an', nombre='Account_another', saldo_inicial=50200)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=2300)
        mov.account_out = accnew
        mov.save()
        self.assertIn(mov, accnew.movements_out.all())

    def test_si_cta_entrada_se_convierte_en_cta_salida_mov_desaparece_de_movements_in(self):
        """ Acción:    La cuenta de entrada se convierte en cuenta de salida
            Chequear:  El movimiento debe eliminarse de los movimientos de entrada
                       de la cuenta"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=25000)
        mov = create_movement(cuenta_in=acc, monto=3322)
        mov.account_out = mov.account_in
        mov.account_in = None
        mov.save()
        self.assertNotIn(mov, acc.movements_in.all())

    def test_si_cta_entrada_se_convierte_en_cta_salida_mov_se_agrega_a_movements_out(self):
        """ Acción:    La cuenta de entrada se convierte en cuenta de salida
            Chequear:  El movimiento debe agregarse a los movimientos de salida
                       de la cuenta"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=25000)
        mov = create_movement(cuenta_in=acc, monto=3322)
        mov.account_out = mov.account_in
        mov.account_in = None
        mov.save()
        self.assertIn(mov, acc.movements_out.all())

    def test_si_cta_entrada_es_cambiada_por_cta_salida_distinta_mov_desaparece_de_movements_in_en_cta_anterior(self):
        """ Acción:    La cuenta de entrada de un movimiento cambia por una cuenta
                       de salida diferente
            Chequear:  El movimiento debe eliminarse de los movimientos
                       de la vieja cuenta de entrada"""
        accinold = create_account(cod='aio', nombre='Account_in_old', saldo_inicial=22000)
        accoutnew = create_account(cod='aon', nombre='Account_out_new', saldo_inicial=44222)
        mov = create_movement(cuenta_in=accinold, monto=223)
        mov.account_out = accoutnew
        mov.account_in = None
        mov.save()
        self.assertNotIn(mov, accinold.movements_in.all())

    def test_si_cta_entrada_es_cambiada_por_cta_salida_distinta_mov_se_agrega_a_movements_out_en_nueva_cta(self):
        """ Acción:    La cuenta de entrada de un movimiento cambia por una cuenta
                       de salida diferente
            Chequear:  El movimiento debe agregarse a los movimientos
                       de la nueva cuenta de salida"""
        accinold = create_account(cod='aio', nombre='Account_in_old', saldo_inicial=22000)
        accoutnew = create_account(cod='aon', nombre='Account_out_new', saldo_inicial=44222)
        mov = create_movement(cuenta_in=accinold, monto=223)
        mov.account_out = accoutnew
        mov.account_in = None
        mov.save()
        self.assertIn(mov, accoutnew.movements_out.all())

    def test_si_cta_salida_se_convierte_en_cta_entrada_mov_desaparece_de_movements_out(self):
        """ Acción:    La cuenta de salida se convierte en cuenta de entrada
            Chequear:  El movimiento debe eliminarse de los movimientos de salida
                       de la cuenta"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=25000)
        mov = create_movement(cuenta_out=acc, monto=3322)
        mov.account_in = mov.account_out
        mov.account_out = None
        mov.save()
        self.assertNotIn(mov, acc.movements_out.all())

    def test_si_cta_salida_se_convierte_en_cta_entrada_mov_se_agrega_a_movements_in(self):
        """ Acción:    La cuenta de salida se convierte en cuenta de entrada
            Chequear:  El movimiento debe agregarse a los movimientos de entrada
                       de la cuenta"""
        acc = create_account(cod='act', nombre='Account', saldo_inicial=25000)
        mov = create_movement(cuenta_out=acc, monto=3322)
        mov.account_in = mov.account_out
        mov.account_out = None
        mov.save()
        self.assertIn(mov, acc.movements_in.all())

    def test_si_cta_salida_es_cambiada_por_cta_entrada_distinta_mov_desaparece_de_movements_out_en_cta_anterior(self):
        """ Acción:    La cuenta de salida de un movimiento cambia por una cuenta
                       de entrada diferente
            Chequear:  El movimiento debe eliminarse de los movimientos
                       de la vieja cuenta de salida"""
        accoutold = create_account(cod='aoo', nombre='Account_in_old', saldo_inicial=22000)
        accinnew = create_account(cod='ain', nombre='Account_out_new', saldo_inicial=44222)
        mov = create_movement(cuenta_out=accoutold, monto=223)
        mov.account_in = accinnew
        mov.account_out = None
        mov.save()
        self.assertNotIn(mov, accoutold.movements_out.all())

    def test_si_cta_salida_es_cambiada_por_cta_entrada_distinta_mov_se_agreaga_a_movements_in_en_nueva_cta(self):
        """ Acción:    La cuenta de salida de un movimiento cambia por una cuenta
                       de entrada diferente
            Chequear:  El movimiento debe agregarse a los movimientos
                       de la nueva cuenta de entrada"""
        accoutold = create_account(cod='aoo', nombre='Account_in_old', saldo_inicial=22000)
        accinnew = create_account(cod='ain', nombre='Account_out_new', saldo_inicial=44222)
        mov = create_movement(cuenta_out=accoutold, monto=223)
        mov.account_in = accinnew
        mov.account_out = None
        mov.save()
        self.assertIn(mov, accinnew.movements_in.all())

    def test_si_mov_salida_cambia_a_mov_trans_se_agrega_movimiento_a_cta_entrada(self):
        """ Acción:     Un movimiento de salida se convierte en movimiento
                        de traspaso.
            Chequear:   El movimiento debe agregarse a los movimientos
                        de la nueva cuenta de entrada"""
        accinnew = create_account(cod='ain', nombre='Account_in_new', saldo_inicial=34555)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=55444)
        mov = create_movement(cuenta_out=accout, monto=5534)
        mov.account_in = accinnew
        mov.save()
        self.assertIn(mov, accinnew.movements_in.all())

    def test_si_mov_entrada_cambia_a_mov_trans_se_agrega_mov_a_cta_salida(self):
        """ Acción:     Un movimiento de entrada se convierte en movimiento
                        de traspaso.
            Chequear:   El movimiento debe agregarse a los movimientos
                        de la nueva cuenta de salida"""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=34555)
        accoutnew = create_account(cod='aon', nombre='Account_out_new', saldo_inicial=55444)
        mov = create_movement(cuenta_in=accin, monto=5534)
        mov.account_out = accoutnew
        mov.save()
        self.assertIn(mov, accoutnew.movements_out.all())

    def test_si_mov_trans_cambia_a_mov_salida_se_elimina_mov_de_cta_entrada(self):
        """ Acción:     Un movimiento de traspaso se convierte en movimiento
                        de salida.
            Chequear:   El movimiento debe eliminarse de los movimientos
                        de la vieja cuenta de entrada"""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=34555)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=55444)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=5534)
        mov.account_in = None
        mov.save()
        self.assertNotIn(mov, accin.movements_in.all())

    def test_si_mov_trans_cambia_a_mov_entrada_se_elimina_mov_de_cta_salida(self):
        """ Acción:     Un movimiento de traspaso se convierte en movimiento
                        de entrada.
            Chequear:   El movimiento debe eliminarse de los movimientos
                        de la vieja cuenta de salida"""
        accin = create_account(cod='ai', nombre='Account_in', saldo_inicial=34555)
        accout = create_account(cod='ao', nombre='Account_out', saldo_inicial=55444)
        mov = create_movement(cuenta_in=accin, cuenta_out=accout, monto=5534)
        mov.account_out = None
        mov.save()
        self.assertNotIn(mov, accout.movements_out.all())
        pass

    def test_si_mov_trans_intercambia_ctas_se_elimina_mov_de_movements_in_en_cta_entrada_anterior(self):
        """ Acción:    En un movimiento de traspaso, se intercambian la cuenta de
                       entrada y la de salida
            Chequear:  El movimiento debe eliminarse de los movimientos de entrada 
                       de la vieja cuenta de entrada."""
        acc1 = create_account(cod='ac1', nombre='Account_1', saldo_inicial=22444)
        acc2 = create_account(cod='ac2', nombre='Account_2', saldo_inicial=35553)
        mov = create_movement(cuenta_in=acc1, cuenta_out=acc2, monto=3355)
        acc = mov.account_in
        mov.account_in = mov.account_out
        mov.account_out = acc
        mov.save()
        self.assertNotIn(mov, acc1.movements_in.all())

    def test_si_mov_trans_intercambia_ctas_se_agrega_mov_a_movements_in_en_nueva_cta_entrada(self):
        """ Acción:    En un movimiento de traspaso, se intercambian la cuenta de
                       entrada y la de salida
            Chequear:  El movimiento debe agregarse a los movimientos de salida 
                       de la vieja cuenta de entrada."""
        acc1 = create_account(cod='a1', nombre='Account_1', saldo_inicial=22444)
        acc2 = create_account(cod='a2', nombre='Account_2', saldo_inicial=35553)
        mov = create_movement(cuenta_in=acc1, cuenta_out=acc2, monto=3355)
        acc = mov.account_in
        mov.account_in = mov.account_out
        mov.account_out = acc
        mov.save()
        self.assertIn(mov, acc1.movements_out.all())

    def test_si_mov_trans_intercambia_ctas_se_elimina_mov_de_movements_out_en_cta_salida_anterior(self):
        """ Acción:    En un movimiento de traspaso, se intercambian la cuenta de
                       entrada y la de salida
            Chequear:  El movimiento debe eliminarse de los movimientos de salida 
                       de la vieja cuenta de salida."""
        acc1 = create_account(cod='ac1', nombre='Account_1', saldo_inicial=22444)
        acc2 = create_account(cod='ac2', nombre='Account_2', saldo_inicial=35553)
        mov = create_movement(cuenta_in=acc1, cuenta_out=acc2, monto=3355)
        acc = mov.account_in
        mov.account_in = mov.account_out
        mov.account_out = acc
        mov.save()
        self.assertNotIn(mov, acc2.movements_out.all())

    def test_si_mov_trans_intercambia_ctas_se_agrega_mov_a_movements_out_en_nueva_cta_salida(self):
        """ Acción:    En un movimiento de traspaso, se intercambian la cuenta de
                       entrada y la de salida
            Chequear:  El movimiento debe agregarse a los movimientos de entrada 
                       de la vieja cuenta de salida."""
        acc1 = create_account(cod='ac1', nombre='Account_1', saldo_inicial=22444)
        acc2 = create_account(cod='ac2', nombre='Account_2', saldo_inicial=35553)
        mov = create_movement(cuenta_in=acc1, cuenta_out=acc2, monto=3355)
        acc = mov.account_in
        mov.account_in = mov.account_out
        mov.account_out = acc
        mov.save()
        self.assertIn(mov, acc2.movements_in.all())

    def test_si_mov_trans_intercambia_ctas_y_cambia_cta_entrada_se_elimina_mov_de_movements_in_en_cta_cambiada_a_salida(self):
        """ Acción:    En un movimiento de traspaso, la cuenta de salida se cambia
                       por la de entrada, que a su vez es reemplazada por una
                       cuenta nueva.
            Chequear:  El movimiento debe eliminarse los movimientos de entrada 
                       de la cuenta que ahora es de salida."""
        accinold = create_account(cod='aio', nombre='Account_in_old', saldo_inicial=22444)
        accoutold = create_account(cod='aoo', nombre='Account_out_old', saldo_inicial=35553)
        accinnew = create_account(cod='ain', nombre='Account_in_new', saldo_inicial=87409)
        mov = create_movement(cuenta_in=accinold, cuenta_out=accoutold, monto=234)

        mov.account_out = mov.account_in
        mov.account_in = accinnew
        mov.save()

        self.assertNotIn(mov, mov.account_out.movements_in.all())

    def test_si_mov_trans_intercambia_ctas_y_cambia_cta_entrada_se_agrega_mov_a_movements_out_en_cta_cambiada_a_salida(self):
        """ Acción:    En un movimiento de traspaso, la cuenta de salida se cambia
                       por la de entrada, que a su vez es reemplazada por una
                       cuenta nueva.
            Chequear:  El movimiento debe agregarse a los movimientos de salida 
                       de la cuenta que ahora es de salida."""
        accinold = create_account(cod='aio', nombre='Account_in_old', saldo_inicial=22444)
        accoutold = create_account(cod='aoo', nombre='Account_out_old', saldo_inicial=35553)
        accinnew = create_account(cod='ain', nombre='Account_in_new', saldo_inicial=87409)
        mov = create_movement(cuenta_in=accinold, cuenta_out=accoutold, monto=234)

        mov.account_out = mov.account_in
        mov.account_in = accinnew
        mov.save()

        self.assertIn(mov, mov.account_out.movements_out.all())

    def test_si_mov_trans_intercambia_ctas_y_cambia_cta_entrada_se_agrega_mov_a_movements_in_en_nueva_cta_entrada(self):
        """ Acción:    En un movimiento de traspaso, la cuenta de salida se cambia
                       por la de entrada, que a su vez es reemplazada por una
                       cuenta nueva.
            Chequear:  El movimiento debe agregarse a los movimientos de entrada 
                       de la nueva cuenta de entrada."""
        accinold = create_account(cod='aio', nombre='Account_in_old', saldo_inicial=22444)
        accoutold = create_account(cod='aoo', nombre='Account_out_old', saldo_inicial=35553)
        accinnew = create_account(cod='ain', nombre='Account_in_new', saldo_inicial=87409)
        mov = create_movement(cuenta_in=accinold, cuenta_out=accoutold, monto=234)

        mov.account_out = mov.account_in
        mov.account_in = accinnew
        mov.save()

        self.assertIn(mov, accinnew.movements_in.all())

    def test_si_mov_trans_intercambia_ctas_y_cambia_cta_salida_se_elimina_mov_de_movements_out_en_cta_intercambiada_a_entrada(self):
        """ Acción:    En un movimiento de traspaso, la cuenta de entrada se cambia
                       por la de salida, que a su vez es reemplazada por una
                       cuenta nueva.
            Chequear:  El movimiento debe eliminarse los movimientos de salida 
                       de la cuenta que ahora es de entrada."""
        accinold = create_account(cod='aio', nombre='Account_in_old', saldo_inicial=22444)
        accoutold = create_account(cod='aoo', nombre='Account_out_old', saldo_inicial=35553)
        accoutnew = create_account(cod='aon', nombre='Account_in_new', saldo_inicial=87409)
        mov = create_movement(cuenta_in=accinold, cuenta_out=accoutold, monto=234)

        mov.account_in = mov.account_out
        mov.account_out = accoutnew
        mov.save()

        self.assertNotIn(mov, mov.account_in.movements_out.all())

    def test_si_mov_trans_intercambia_ctas_y_cambia_cta_salida_se_agrega_mov_a_movements_in_en_cta_intercambiada_a_entrada(self):
        """ Acción:    En un movimiento de traspaso, la cuenta de entrada se cambia
                       por la de salida, que a su vez es reemplazada por una
                       cuenta nueva.
            Chequear:  El movimiento debe agregarse a los movimientos de entrada 
                       de la cuenta que ahora es de entrada."""
        accinold = create_account(cod='aio', nombre='Account_in_old', saldo_inicial=22444)
        accoutold = create_account(cod='aoo', nombre='Account_out_old', saldo_inicial=35553)
        accoutnew = create_account(cod='aon', nombre='Account_in_new', saldo_inicial=87409)
        mov = create_movement(cuenta_in=accinold, cuenta_out=accoutold, monto=234)

        mov.account_in = mov.account_out
        mov.account_out = accoutnew
        mov.save()

        self.assertIn(mov, mov.account_in.movements_in.all())

    def test_si_mov_trans_intercambia_ctas_y_cambia_cta_salida_se_agrega_mov_a_movements_out_en_nueva_cta_salida(self):
        """ Acción:    En un movimiento de traspaso, la cuenta de entrada se cambia
                       por la de salida, que a su vez es reemplazada por una
                       cuenta nueva.
            Chequear:  El movimiento debe agregarse a los movimientos de salida
                       de nueva cuenta de salida."""
        accinold = create_account(cod='aio', nombre='Account_in_old', saldo_inicial=22444)
        accoutold = create_account(cod='aoo', nombre='Account_out_old', saldo_inicial=35553)
        accoutnew = create_account(cod='aon', nombre='Account_in_new', saldo_inicial=87409)
        mov = create_movement(cuenta_in=accinold, cuenta_out=accoutold, monto=234)

        mov.account_in = mov.account_out
        mov.account_out = accoutnew
        mov.save()

        self.assertIn(mov, accoutnew.movements_out.all())

    def test_saldo_inicial_mas_movimientos_es_igual_a_saldo_final(self):
        """ Comprueba que el saldo final de cada cuenta coincide con el saldo
            inicial al que se le han aplicado los movimientos
        """
        accin = create_account(cod='ai', nombre='Account1', saldo_inicial=1400)
        accout = create_account(cod='ao', nombre='Account2', saldo_inicial=1900)
        create_movement(cuenta_in=accin, monto=220)
        create_movement(cuenta_out=accin, monto=500)
        create_movement(cuenta_in=accin, cuenta_out=accout, monto=700)
        saldo = accin.balance

        for mov in accin.movements_in.all():
            saldo = saldo - mov.amount
        for mov in accin.movements_out.all():
            saldo = saldo + mov.amount

        self.assertEqual(accin.balance_start, saldo)

    def test_saldo_inicial_mas_movimientos_aleatorios_es_igual_a_saldo_final(self):
        """ Comprueba que el saldo final de cada cuenta coincide con el saldo
            inicial al que se le han aplicado movimientos con valores al azar
        """

        TWOPLACES = decimal.Decimal(10) ** -2

        accin = create_account(cod='ai', nombre='Account1', saldo_inicial=1400)
        accout = create_account(cod='ao', nombre='Account2', saldo_inicial=1900)

        direction = 0
        for x in range(100):
            montorandom = decimal.Decimal(random.uniform(0, 99999)). \
                quantize(TWOPLACES)
            if direction == 0:
                mov = create_movement(cuenta_in=accin, monto=montorandom)
                direction += 1
            elif direction == 1:
                mov = create_movement(cuenta_out=accin, monto=montorandom)
                direction += 1
            elif direction == 2:
                mov = create_movement(cuenta_in=accout, cuenta_out=accin,
                                      monto=montorandom)
            else:
                mov = create_movement(cuenta_in=accin, cuenta_out=accout,
                                      monto=montorandom)
                direction = 0

        sum_mov_in = accin.movements_in.aggregate(Sum('amount'))['amount__sum']
        sum_mov_out = accin.movements_out.aggregate(Sum('amount'))['amount__sum']

        saldo_inicial = accin.balance - sum_mov_in + sum_mov_out

        self.assertEqual(accin.balance_start, saldo_inicial)
