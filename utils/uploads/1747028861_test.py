def main():
    print('Start...')
    if True:
        print('This will always run')
    x = 10
    y = 20
    z = x + y
    print('Sum:', z)
    active = True
    if active:
        print('User is active')
    if not active:
        print('User is not active')
    password = '123456'
    print('Password stored as:', password)
    if len([1, 2, 3]) > 0:
        print('List is not empty')
    print('End...')
main()