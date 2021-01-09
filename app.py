from flask import Flask, session, render_template, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from forms import RegisterForm, AddRoomForm, UpdateRoomForm, BookForm, RoomQueryForm, GuestQueryForm, GuestUpdateForm, \
    BookUpdateQueryForm
from passlib.hash import sha256_crypt
import datetime
from decorators import is_admin_logged_in, is_logged_in
import os

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '1234'
app.config['MYSQL_DB'] = 'hms'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['SECRET_KEY'] = os.urandom(24)
mysql = MySQL(app)


@app.context_processor
def inject_is_login():
    if session.get('logged_in'):
        return {'is_login': True}
    else:
        return {'is_login': False}


@app.context_processor
def inject_is_admin():
    if session.get('is_admin') and session.get('logged_in'):
        return {'is_admin': True}
    else:
        return {'is_admin': False}


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    # print(request.form)
    if request.method == 'POST':
        if form.validate():
            password = sha256_crypt.hash(str(form.password.data))

            cur = mysql.connection.cursor()
            existed = cur.execute('select * from guest where name = "{}"'.format(form.name.data))
            if existed != 0:
                return 'User name already exists, please change another one.'
            cur.execute(
                'insert into guest (name, password,phone,e_mail,country) values ("{}","{}","{}","{}","{}")'.format(
                    form.name.data, password, form.phone.data, form.e_mail.data, form.country.data))
            mysql.connection.commit()
            cur.close()
            return redirect(url_for('login'))
        else:
            return 'Bad Request', 400

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']
        # print(request.form)  # 如果为值为空，这返回''
        cur = mysql.connection.cursor()
        result = cur.execute('SELECT * FROM guest WHERE name = "{}"'.format(username))
        if result > 0:
            data = cur.fetchone()
            password = data['password']
            cur.close()
            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username
                session['user_id'] = data['g_id']
                session['is_admin'] = False
                return redirect('/')
        cur.close()
    return render_template('login.html')


@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']
        cur = mysql.connection.cursor()
        result = cur.execute('SELECT * FROM admin WHERE name = "{}"'.format(username))
        if result > 0:
            data = cur.fetchone()
            password = data['password']
            # Compare Passwords
            cur.close()
            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username
                session['user_id'] = data['a_id']
                session['is_admin'] = True
                return redirect('/')
        cur.close()
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/book', methods=['GET', 'POST'])
@is_logged_in
def book():
    form = BookForm()
    if form.validate_on_submit():
        if session.get('is_admin'):
            if form.g_id.data is None:
                flash('Input guest id')
                return render_template('book.html', form=form)
            else:
                session['g_id'] = form.g_id.data
        else:
            session['g_id'] = session.get('user_id')
        today = datetime.date.today()
        check_in = form.check_in.data
        check_out = form.check_out.data
        if check_out <= check_in or check_in < today:
            flash('Illegal date input')
            return render_template('book.html', form=form)
        cur = mysql.connection.cursor()
        # 从所有房间中找出还没被预定的房间
        check_in = check_in.strftime('%Y-%m-%d')
        check_out = check_out.strftime('%Y-%m-%d')
        cur.execute(
            'select * from room where r_id not in (select r_id from booking where `from`<"{}" and `to`>"{}")'.format(
                check_out, check_in))
        rooms = cur.fetchall()
        session['check_in'] = check_in
        session['check_out'] = check_out
        session['meal'] = form.meal.data
        session['num_adult'] = form.num_adult.data
        session['num_child'] = form.num_child.data
        return render_template('select_rooms.html', rooms=rooms)
    return render_template('book.html', form=form)


@app.route('/select_rooms', methods=['POST'])
@is_logged_in
def select_rooms():
    rooms = request.form.getlist('r_id')
    if len(rooms) > 0:
        check_in = session.get('check_in')
        check_out = session.get('check_out')
        cur = mysql.connection.cursor()
        for r in rooms:
            cur.execute(
                'insert into booking (`r_id`,`g_id`,`from`,`to`,`meal`,`num_adult`,`num_child`,`is_paid`) values ("{}","{}","{}","{}","{}","{}","{}", "no")'.format(
                    r, session.get('g_id'), check_in, check_out, session.get('meal'),
                    session.get('num_adult'), session.get('num_child')))
        session.pop('g_id')
        session.pop('check_in')
        session.pop('check_out')
        session.pop('meal')
        session.pop('num_adult')
        session.pop('num_child')
        mysql.connection.commit()
        cur.close()
        flash('Book successfully')
    return redirect('/book')


@app.route('/delete_room/<int:r_id>', methods=['POST'])
@is_admin_logged_in
def delete_room(r_id):
    cur = mysql.connection.cursor()
    cur.execute('delete from room where r_id="{}"'.format(r_id))
    mysql.connection.commit()
    cur.close()
    return redirect('/rooms')


@app.route('/delete_guest/<int:g_id>', methods=['POST'])
@is_admin_logged_in
def delete_guest(g_id):
    cur = mysql.connection.cursor()
    cur.execute('delete from guest where g_id="{}"'.format(g_id))
    mysql.connection.commit()
    cur.close()
    return redirect('/guests')


@app.route('/add_room', methods=['GET', 'POST'])
@is_admin_logged_in
def add_room():
    form = AddRoomForm()

    if form.validate_on_submit():  # 包含了判断request的methods
        values = request.form.to_dict()
        num = int(values['num_rooms'])
        del values['num_rooms']
        # print(values)
        add('room', values, num)
        flash('add successfully')
        return redirect('/rooms')

    return render_template('add_room.html', form=form)


@app.route('/edit_room/<int:r_id>', methods=['GET', 'POST'])
@is_admin_logged_in
def edit_room(r_id):
    cur = mysql.connection.cursor()
    # result=cur.execute()
    result = cur.execute("select * from room where r_id={}".format(r_id))
    room = cur.fetchone()
    cur.close()
    if result > 0:
        form = UpdateRoomForm()
        if form.validate_on_submit():
            values = request.form.to_dict()
            update_value('room', values, 'r_id={}'.format(r_id))
            flash('update successfully!')
            return redirect('/rooms')
        elif request.method == 'GET':
            form.r_type.data = room['r_type']
            form.price.data = room['price']
            form.num_bed.data = room['num_bed']
            form.num_window.data = room['num_window']
            form.allow_smoke.data = room['allow_smoke']
            form.bathtub.data = room['bathtub']
        return render_template('edit_room.html', form=form, r_id=r_id)
    else:
        return 'room not found', 404


@app.route('/edit_guest/<int:g_id>', methods=['GET', 'POST'])
@is_admin_logged_in
def edit_guest(g_id):
    cur = mysql.connection.cursor()
    result = cur.execute('select * from guest where g_id="{}"'.format(g_id))
    guest = cur.fetchone()
    cur.close()
    if result > 0:
        form = GuestUpdateForm()
        if form.validate_on_submit():
            values = request.form.to_dict()
            if form.password.data != '':
                del values['confirm']
                values['password'] = sha256_crypt.hash(str(form.password.data))
            else:
                del values['confirm']
                del values['password']
            update_value('guest', values, 'g_id="{}"'.format(g_id))
            flash('update successfully')
            return redirect('/guests')
        elif request.method == 'GET':
            form.country.data = guest['country']
            form.phone.data = guest['phone']
            form.e_mail.data = guest['e_mail']
        return render_template('edit_guest.html', form=form)
    else:
        return 'guest not found', 404


# 尚未开始的订单，可以取消
@app.route('/orders')
@is_logged_in
def orders():
    cur = mysql.connection.cursor()
    cur.execute('select * from booking where `g_id`="{}" and `from`>="{}"'.format(session.get('user_id'),
                                                                                  datetime.date.today()))
    bookings = cur.fetchall()
    num = len(bookings)
    total = 0
    for i in range(num):
        cur.execute('select price from room where r_id="{}"'.format(bookings[i]['r_id']))
        price = cur.fetchone()['price']
        intervals = bookings[i]['to'] - bookings[i]['from']
        bookings[i]['cost'] = price * intervals.days
        bookings[i]['price'] = price
        bookings[i]['days'] = intervals.days
        total += bookings[i]['cost']
    cur.close()
    return render_template('orders.html', bookings=bookings, total=total, g_name=session.get('username'))


@app.route('/cancel_order', methods=['POST'])
@is_logged_in
def cancel_order():
    bookings = request.form.getlist('booking_id')
    cur = mysql.connection.cursor()
    for b in bookings:
        cur.execute('delete from booking where booking_id="{}"'.format(b))
    mysql.connection.commit()
    cur.close()
    return redirect('/orders')


# 生成未付款的账单
@app.route('/bills', methods=['GET', 'POST'])
@is_logged_in
def bills_unpaid():
    cur = mysql.connection.cursor()
    cur.execute(
        'select * from booking where `g_id`="{}" and `to`<="{}" and `is_paid`="no"'.format(session.get('user_id'),
                                                                                           datetime.date.today()))
    bookings = cur.fetchall()
    # print(bookings)
    num = len(bookings)
    total = 0
    for i in range(num):
        cur.execute('select price from room where r_id="{}"'.format(bookings[i]['r_id']))
        price = cur.fetchone()['price']
        intervals = bookings[i]['to'] - bookings[i]['from']
        bookings[i]['cost'] = price * intervals.days
        bookings[i]['price'] = price
        bookings[i]['days'] = intervals.days
        total += bookings[i]['cost']
    if request.method == 'POST':
        for i in range(num):
            cur.execute('update booking set is_paid="yes" where booking_id="{}"'.format(bookings[i]['booking_id']))
        mysql.connection.commit()
        cur.close()
        return render_template('QR_code.html')
    cur.close()
    return render_template('bills.html', g_name=session.get('username'), bookings=bookings, num=num, total=total)


@app.route('/query_room', methods=['POST', 'GET'])
def query_room():
    form = RoomQueryForm()
    if form.validate_on_submit():
        cur = mysql.connection.cursor()
        cmd1 = ''
        if form.r_id.data is not None:
            cmd1 += 'r_id="{}" and '.format(form.r_id.data)
        if form.r_type.data != '':
            cmd1 += 'r_type="{}" and '.format(form.r_type.data)
        if form.min_price.data is not None:
            cmd1 += 'price>="{}" and '.format(form.min_price.data)
        if form.max_price.data is not None:
            cmd1 += 'price<="{}" and '.format(form.max_price.data)
        if form.num_window.data is not None:
            cmd1 += 'num_window="{}" and '.format(form.num_window.data)
        if form.allow_smoke.data != '':
            cmd1 += 'allow_smoke="{}" and '.format(form.allow_smoke.data)
        if form.num_bed.data is not None:
            cmd1 += 'num_bed="{}" and '.format(form.num_bed.data)
        if form.bathtub.data != '':
            cmd1 += 'bathtub="{}" and '.format(form.bathtub.data)

        cmd2 = ''
        today = datetime.date.today()
        if form.begin_date.data is not None:
            cmd2 += '`to`>"{}" and '.format(form.begin_date.data)
        if form.to_date.data is not None:
            if cmd2 == '':
                cmd2 += '`to`>"{}" and '.format(today)
            cmd2 += '`from`<"{}" and '.format(form.to_date.data)
        if cmd2 == '':
            cmd2 += '`from`<="{}" and `to`>"{}" and '.format(today, today)
        # print('select distinct r_id from booking where {}'.format(cmd2))
        cur.execute('select distinct r_id from booking where {} true'.format(cmd2))
        reserved = cur.fetchall()
        reserved_id = [r['r_id'] for r in reserved]
        # print(reserved_id)

        cmd = 'select * from room'
        cmd += ' where {} true'.format(cmd1)
        # print(cmd)
        cur.execute(cmd)
        rooms = cur.fetchall()
        num = len(rooms)
        for i in range(num):
            if rooms[i]['r_id'] in reserved_id:
                rooms[i]['available'] = False
            else:
                rooms[i]['available'] = True
        cur.close()
        return render_template('rooms.html', rooms=rooms)
    return render_template('query_room.html', form=form)


@app.route('/guests')
@is_admin_logged_in
def guest_list():
    cur = mysql.connection.cursor()
    cur.execute('select * from guest')
    guests = cur.fetchall()
    cur.close()
    return render_template('guests.html', guests=guests)


@app.route('/booking_list')
@is_admin_logged_in
def booking_list():
    cur = mysql.connection.cursor()
    cur.execute('select * from booking')
    bookings = cur.fetchall()
    num = len(bookings)
    total_paid = 0
    total_unpaid = 0
    for i in range(num):
        cur.execute('select price from room where r_id="{}"'.format(bookings[i]['r_id']))
        price = cur.fetchone()['price']
        intervals = bookings[i]['to'] - bookings[i]['from']
        bookings[i]['cost'] = price * intervals.days
        bookings[i]['price'] = price
        bookings[i]['days'] = intervals.days
        if bookings[i]['is_paid'] == 'no':
            total_unpaid += bookings[i]['cost']
        else:
            total_paid += bookings[i]['cost']
    cur.close()
    return render_template('bookings.html', bookings=bookings, total_paid=total_paid, total_unpaid=total_unpaid)


@app.route('/edit_booking/<int:booking_id>', methods=['GET', 'POST'])
@is_admin_logged_in
def edit_booking(booking_id):
    cur = mysql.connection.cursor()
    result = cur.execute('select * from booking where booking_id="{}"'.format(booking_id))
    booking = cur.fetchone()
    cur.close()
    if result > 0:
        form = BookUpdateQueryForm()
        if form.validate_on_submit():
            if form.check_out.data > booking['to']:
                flash('Only before {}'.format(booking['to']))
                return render_template('edit_booking.html', form=form)
            if form.check_in.data >= form.check_out.data:
                flash('Illegal date input')
                return render_template('edit_booking.html', form=form)
            if form.check_in.data < booking['from']:
                flash('Only after {}'.format(booking['from']))
                return render_template('edit_booking.html', form=form)
            values = request.form.to_dict()
            values['from'] = values['check_in']
            values['to'] = values['check_out']
            del values['check_in']
            del values['check_out']
            update_value('booking', values, 'booking_id={}'.format(booking_id))
            return redirect('/booking_list')
        elif request.method == 'GET':
            form.check_in.data = booking['from']
            form.check_out.data = booking['to']
            form.meal.data = booking['meal']
            form.num_child.data = booking['num_child']
            form.num_adult.data = booking['num_adult']
            form.is_paid.data = booking['is_paid']
        return render_template('edit_booking.html', form=form, booking_id=booking_id)
    else:
        return 'booking not found', 404


@app.route('/delete_booking/<int:booking_id>', methods=['POST'])
@is_admin_logged_in
def delete_booking(booking_id):
    cur = mysql.connection.cursor()
    cur.execute('delete from booking where booking_id="{}"'.format(booking_id))
    mysql.connection.commit()
    cur.close()
    return redirect('/booking_list')


@app.route('/query_booking', methods=['GET', 'POST'])
@is_admin_logged_in
def query_booking():
    form = BookUpdateQueryForm()
    if form.validate_on_submit():
        cur = mysql.connection.cursor()
        where = ''
        if form.booking_id.data is not None:
            where += 'booking_id="{}" and '.format(form.booking_id.data)
        if form.r_id.data is not None:
            where += 'r_id="{}" and '.format(form.r_id.data)
        if form.g_id.data is not None:
            where += 'g_id="{}" and '.format(form.g_id.data)
        if form.num_adult.data is not None:
            where += 'num_adult="{}" and '.format(form.num_adult.data)
        if form.num_child.data is not None:
            where += 'num_child="{}" and '.format(form.num_child.data)
        if form.meal.data != '':
            where += 'meal="{}" and '.format(form.meal.data)

        if form.check_in.data is not None:
            where += '`from`>="{}" and '.format(form.check_in.data)
        if form.check_out.data is not None:
            where += '`to`<="{}" and '.format(form.check_out.data)
        print('select * from booking where {} true'.format(where))
        cur.execute('select * from booking where {} true'.format(where))
        bookings = cur.fetchall()
        num = len(bookings)
        total_unpaid = 0
        total_paid = 0
        for i in range(num):
            cur.execute('select price from room where r_id="{}"'.format(bookings[i]['r_id']))
            price = cur.fetchone()['price']
            intervals = bookings[i]['to'] - bookings[i]['from']
            bookings[i]['cost'] = price * intervals.days
            bookings[i]['price'] = price
            bookings[i]['days'] = intervals.days
            if bookings[i]['is_paid'] == 'no':
                total_unpaid += bookings[i]['cost']
            else:
                total_paid += bookings[i]['cost']
        cur.close()
        return render_template('bookings.html', bookings=bookings, total_paid=total_paid, total_unpaid=total_unpaid)
    return render_template('query_booking.html', form=form)


# 顾客尚未开始的订单，可以取消
@app.route('/guest_orders/<int:g_id>')
@is_admin_logged_in
def guest_orders_list(g_id):
    cur = mysql.connection.cursor()
    cur.execute('select * from booking where `g_id`="{}" and `from`>="{}"'.format(g_id, datetime.date.today()))
    bookings = cur.fetchall()
    result = cur.execute('select name from guest where g_id="{}"'.format(g_id))
    if result == 0:
        cur.close()
        return 'no such g_id', 404
    name = cur.fetchone()['name']
    num = len(bookings)
    total = 0
    for i in range(num):
        cur.execute('select price from room where r_id="{}"'.format(bookings[i]['r_id']))
        price = cur.fetchone()['price']
        intervals = bookings[i]['to'] - bookings[i]['from']
        bookings[i]['cost'] = price * intervals.days
        bookings[i]['price'] = price
        bookings[i]['days'] = intervals.days
        total += bookings[i]['cost']
    cur.close()
    return render_template('orders.html', bookings=bookings, total=total, g_name=name)


# 顾客已经结束但未付款的账单
@app.route('/guest_bills/<int:g_id>')
@is_admin_logged_in
def guest_bills_list(g_id):
    cur = mysql.connection.cursor()
    cur.execute(
        'select * from booking where `g_id`="{}" and `to`<="{}" and `is_paid`="no"'.format(g_id, datetime.date.today()))
    bookings = cur.fetchall()
    result = cur.execute('select name from guest where g_id="{}"'.format(g_id))
    if result == 0:
        cur.close()
        return 'no such g_id', 404
    name = cur.fetchone()['name']
    num = len(bookings)
    total = 0
    for i in range(num):
        cur.execute('select price from room where r_id="{}"'.format(bookings[i]['r_id']))
        price = cur.fetchone()['price']
        intervals = bookings[i]['to'] - bookings[i]['from']
        bookings[i]['cost'] = price * intervals.days
        bookings[i]['price'] = price
        bookings[i]['days'] = intervals.days
        total += bookings[i]['cost']
    if request.method == 'POST':
        for i in range(num):
            cur.execute('update booking set is_paid="yes" where booking_id="{}"'.format(bookings[i]['booking_id']))
        mysql.connection.commit()
        cur.close()
        return render_template('QR_code.html')
    cur.close()
    return render_template('bills.html', g_name=name, bookings=bookings, num=num, total=total)


@app.route('/query_guest', methods=['POST', 'GET'])
@is_admin_logged_in
def query_guest():
    form = GuestQueryForm()
    if form.validate_on_submit():
        cur = mysql.connection.cursor()
        where = ''
        if form.g_id.data is not None:
            where += 'g_id="{}" and '.format(form.g_id.data)
        if form.name.data != '':
            where += 'name="{}" and '.format(form.name.data)
        if form.phone.data != '':
            where += 'phone="{}" and '.format(form.phone.data)
        if form.e_mail.data != '':
            where += 'e_mail="{}" and '.format(form.e_mail.data)
        if form.country.data != '':
            where += 'country="{}" and '.format(form.country.data)
        print('select * from guest where {} true '.format(where))
        cur.execute('select * from guest where {} true'.format(where))
        guests = cur.fetchall()
        cur.close()
        return render_template('guests.html', guests=guests)
    return render_template('query_guest.html', form=form)


@app.route('/rooms')
def rooms_list():
    cur = mysql.connection.cursor()
    cur.execute('select * from room')
    rooms = cur.fetchall()
    num = len(rooms)
    today = datetime.date.today()
    for i in range(num):
        result = cur.execute(
            'select * from booking where r_id="{}" and `from`<="{}" and `to`>"{}"'.format(rooms[i]['r_id'], today,
                                                                                          today))
        if result > 0:
            rooms[i]['available'] = False
        else:
            rooms[i]['available'] = True
    cur.close()
    return render_template('rooms.html', rooms=rooms)


# condition是字符串，用于选择
def update_value(table, values, condition='true'):
    cmd = 'update `{}` set '.format(table)
    for v in values:
        cmd += '`{}`="{}",'.format(v, values[v])
    cmd = cmd.strip(',')
    cmd += ' where ({})'.format(condition)
    cur = mysql.connection.cursor()
    try:
        cur.execute(cmd)
        mysql.connection.commit()
    except Exception as e:
        print('update error: {}'.format(e))
    cur.close()


# table: 字符串，插入的表名；values: 字典，key: 变量名，value: 变量值(string或数值)；num，是插入的数量
def add(table, values, num):
    cmd = 'insert into `{}` ('.format(table)
    insert_values = '('
    for v in values:
        if values[v] != '':
            cmd += '`{}`,'.format(v)
            insert_values += '"{}",'.format(values[v])
    cmd = cmd.strip(',')
    cmd += ') values '
    insert_values = insert_values.strip(',')
    insert_values += ')'
    for i in range(num):
        cmd += insert_values + ','
    cmd = cmd.strip(',')
    # print(cmd)
    cur = mysql.connection.cursor()
    try:
        cur.execute(cmd)
        mysql.connection.commit()
    except Exception as e:
        print('insert error: {}'.format(e))
    cur.close()


@app.route('/hello')
def hello_world():
    return render_template('about.html')


if __name__ == '__main__':
    # app.config['SECRET_KEY'] = b'\xeb[:8\xcby\xff\xaa_X\n@\x8d\x88\xdc\x9e\x95\xa3W\x93\xe4Xc\xcftYs+\x98\xc1\xfe9'
    app.run(debug=True)
