import pymysql
from passlib.hash import sha256_crypt
import getpass

if __name__ == '__main__':
    connection = pymysql.connect(host='localhost', port=3306, user='root', password='1234', database='hms')
    cur = connection.cursor()
    while True:
        name = input('User Name: ')
        result = cur.execute('select * from admin where name="{}"'.format(name))
        if result > 0:
            print('User Name Occupied!')
        else:
            break
    phone = input('Phone: ')
    e_mail = input('E-mail: ')
    while True:
        password = getpass.getpass('Password: ')
        confirm = getpass.getpass('Confirm: ')
        if confirm != password:
            print('Password does not match, input again')
        else:
            break
    password = sha256_crypt.hash(password)
    cur.execute(
        'insert into admin (name,password,phone,e_mail)values ("{}","{}","{}","{}")'.format(name, password, phone,
                                                                                            e_mail))
    connection.commit()
    cur.close()
    connection.close()
