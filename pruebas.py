from finper.models import Account, Category, Movement

a1 = Account.objects.get(id=1)
a2 = Account.objects.get(id=2)
bal = a.balance
c = Category.objects.get(id=1)

m1 = Movement.objects.create(amount=1000, account_out=a1, category=c)
print('Movement.objects.create(amount=1000, account_out = a1, category=c)')
print(bal)
print(f'account_out: {m.account_out}')
print(f'account_in: {m.account_in}')
print(f'account_out.balance: {m.account_out.balance}')

m2 = Movement.objects.create(amount=2000, account_in=a1, category=c)
print('Movement.objects.create(amount=2000, account_in = a1, category=c)')
print(bal)
print(f'account_out: {m.account_out}')
print(f'account_in: {m.account_in}')
print(f'account_in.balance: {m.account_in.balance}')

m3 = Movement.objects.create(amount=3000,
                             account_out=a1,
                             account_in=a2,
                             category=c)
print('Movement.objects.create(amount=1000, account_out = a1, account_in = a2, category=c)')
print(bal)
print(f'account_out: {m.account_out}')
print(f'account_in: {m.account_in}')
print(f'account_out.balance: {m.account_out.balance}')
print(f'account_in.balance: {m.account_in.balance}')
