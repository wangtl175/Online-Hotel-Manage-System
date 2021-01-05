from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, validators, FloatField, IntegerField, DateField, SubmitField


class RegisterForm(FlaskForm):
    name = StringField('Username', [validators.Length(min=1, max=45)])
    e_mail = StringField('Email', [validators.Length(min=6, max=45)])
    country = StringField('Country', [validators.Length(min=1, max=45)])
    phone = StringField('Phone', [validators.Length(min=1, max=45)])
    password = PasswordField('New Password',
                             [validators.DataRequired(), validators.EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Repeat Password')

    class Meta:
        csrf = False


class AddRoomForm(FlaskForm):
    r_type = StringField('Room Type', [validators.Length(min=1, max=45), validators.DataRequired()])
    price = FloatField('Price', [validators.number_range(min=200), validators.DataRequired()])
    num_window = IntegerField('Number of windows', [validators.NumberRange(min=0, max=5), validators.DataRequired()])
    allow_smoke = StringField('Allow smoke', [validators.Length(min=1, max=5), validators.DataRequired()])
    num_bed = IntegerField('Number of beds', [validators.NumberRange(min=1, max=5), validators.DataRequired()])
    bathtub = StringField('bathtub', [validators.Length(min=1, max=45), validators.DataRequired()])
    num_rooms = IntegerField('Number of Rooms', [validators.NumberRange(min=1), validators.DataRequired()])

    class Meta:
        csrf = False


class UpdateRoomForm(FlaskForm):
    r_type = StringField('Room Type', [validators.Length(min=1, max=45), validators.DataRequired()])
    price = FloatField('Price', [validators.number_range(min=200), validators.DataRequired()])
    num_window = IntegerField('Number of windows', [validators.NumberRange(min=0, max=5), validators.DataRequired()])
    allow_smoke = StringField('Allow smoke', [validators.Length(min=1, max=5), validators.DataRequired()])
    num_bed = IntegerField('Number of beds', [validators.NumberRange(min=1, max=5), validators.DataRequired()])
    bathtub = StringField('bathtub', [validators.Length(min=1, max=45)])

    class Meta:
        csrf = False


class BookForm(FlaskForm):
    g_id = IntegerField('Guest ID', validators=[validators.Optional()])
    check_in = DateField('Check in date, eg: 2020-01-01', format='%Y-%m-%d', validators=[validators.DataRequired()])
    check_out = DateField('Check out date, eg: 2020-01-31', format='%Y-%m-%d', validators=[validators.DataRequired()])
    meal = StringField('Need meal?', validators=[validators.Length(max=45)], default='no')
    num_adult = IntegerField('Number of adult each room', validators=[validators.NumberRange(max=4)], default=1)
    num_child = IntegerField('Number of children each room', validators=[validators.NumberRange(max=6)], default=0)

    class Meta:
        csrf = False


class RoomQueryForm(FlaskForm):
    r_id = IntegerField('Room ID', validators=[validators.Optional()])
    begin_date = DateField('Date From, eg: 2021-01-1', format='%Y-%m-%d', validators=[validators.Optional()])
    to_date = DateField('Date To, eg: 2021-01-31', format='%Y-%m-%d', validators=[validators.Optional()])
    r_type = StringField('Room Type', validators=[validators.Length(min=1, max=45), validators.Optional()])
    min_price = FloatField('Min Price', validators=[validators.Optional(), validators.NumberRange(min=0)])
    max_price = FloatField('Max Price', validators=[validators.Optional(), validators.NumberRange(min=0)])
    num_window = IntegerField('Number of windows', validators=[validators.Optional(), validators.NumberRange(min=0)])
    allow_smoke = StringField('Allow smoke', validators=[validators.Length(min=1, max=5), validators.Optional()])
    num_bed = IntegerField('Number of beds', validators=[validators.Optional(), validators.NumberRange(min=0)])
    bathtub = StringField('bathtub', validators=[validators.Length(min=1, max=45), validators.Optional()])

    class Meta:
        csrf = False


class GuestQueryForm(FlaskForm):
    g_id = IntegerField('Guest ID', validators=[validators.Optional()])
    name = StringField('Username', validators=[validators.Length(max=45), validators.Optional()])
    e_mail = StringField('Email', validators=[validators.Length(max=45), validators.Optional()])
    country = StringField('Country', validators=[validators.Length(max=45), validators.Optional()])
    phone = StringField('Phone', validators=[validators.Length(max=45), validators.Optional()])

    class Meta:
        csrf = False


class GuestUpdateForm(FlaskForm):
    e_mail = StringField('Email', [validators.Length(min=6, max=45), validators.Optional()])
    country = StringField('Country', [validators.Length(min=1, max=45), validators.Optional()])
    phone = StringField('Phone', [validators.Length(min=1, max=45), validators.Optional()])
    password = PasswordField('New Password',
                             [validators.Optional(), validators.EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Repeat Password', validators=[validators.Optional()])

    class Meta:
        csrf = False


class BookUpdateQueryForm(FlaskForm):
    booking_id = IntegerField('Booking ID', validators=[validators.Optional()])
    g_id = IntegerField('Guest ID', validators=[validators.Optional()])
    r_id = IntegerField('Room ID', validators=[validators.Optional()])
    check_in = DateField('Check in date, eg: 2021-01-01', format='%Y-%m-%d', validators=[validators.Optional()])
    check_out = DateField('Check out date, eg: 2021-01-31', format='%Y-%m-%d', validators=[validators.Optional()])
    meal = StringField('Need meal?', validators=[validators.Length(max=45), validators.Optional()])
    num_adult = IntegerField('Number of adult each room',
                             validators=[validators.NumberRange(max=4), validators.Optional()])
    num_child = IntegerField('Number of children each room',
                             validators=[validators.NumberRange(max=6), validators.Optional()])
    is_paid = StringField('Is paid?', validators=[validators.Optional(), validators.Length(max=45)])

    class Meta:
        csrf = False
