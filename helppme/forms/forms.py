from helppme.globals import categories as cats
from helppme.models.user import User
from flask.ext.wtf import email, EqualTo, Form, Length, Required, TextField,\
                          TextAreaField, SelectField, SubmitField, URL


class Deal_Form(Form):
    title = TextField("title",
                      validators=[Required(message='This is required')])
    categories = SelectField(u'Group',
                            choices=[(category.title(), category) for category in cats])
    location = TextField("location",
                         validators=[
                            Length(max=300, message="location can't be longer than 300 characters"),
                            URL(message="Doesn't look like a valid link. Valid links should start with http://")
                         ])
    description = TextAreaField('description',
                                 validators=[
                                    Length(max=5000, message="Description can't be longer than 5000 characters")
                                 ])
    submit = SubmitField("Submit")

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            # Hack - if the self.location.data is "", the URL validator
            # will raise an invalid URL error. But the length validator should
            # raise no errors since "" has length < 300.
            #
            # Therefore, if self.location.data is None, we can assume that
            # there is only 1 location error, and the error is invalid URL.
            # Since we want to allow the user to NOT enter a URL, we will
            # to pop the invalid URL error from self.location.error
            if self.location.data == "":
                self.location.errors.pop()
            if len(self.title.data) > 128:
                num = len(self.title.data) - 128
                message = "This is too long by {num} characters"\
                          .format(num=num)
                self.title.errors.append(message)
            if self.title.errors or self.categories.errors or \
                self.location.errors or self.description.errors:
                return False
        return True


class Edit_Form(Form):
    description = TextAreaField('description', validators=[
            Length(max=5000, message="Description can't be longer than 5000 characters")])
    submit = SubmitField("Submit")


class Login_Form(Form):
    username = TextField("username", validators=[Required(message='Username is required')])
    password = TextField("password", validators=[Required(message='Password is required')])
    submit = SubmitField("submit")

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.user = None

    def validate(self):
        rv = Form.validate(self)
        if not rv:
            return False

        user = User.get_user(self.username.data, self.password.data)
        if user is None:
            return False

        self.user = user
        return True


class Password_Reset_Form(Form):
    password = TextField("New Password",
                         validators=[Length(min=6, message="Password must be 6 characters or longer"),
                            Length(max=50, message="Password cannot be longer than 50 characters"),
                            Required(message='Password is required'),
                            EqualTo('confirm', message="Password must match")])

    confirm = TextField("Repeat Password",
                         validators=[Required(message='Please repeat your new password')])


class Password_Request_Form(Form):
    email = TextField("email",
                       validators=[
                            Required(message='Please enter your email address'),
                            email(message='Is this a valid email?')
                        ])


class Signup_Form(Form):
    email = TextField("email", validators=[email(message='Is this a valid email?'),
                        Required(message='Email address is required')])

    username = TextField("username", validators=[Length(min=3, message='Username must be 3 characters or longer'),
                            Length(max=20, message="Username cannot be longer than 20 characters"),
                            Required(message='Username is required')])
    password = TextField("password", validators=[Length(min=6, message="Password must be 6 characters or longer"),
                            Length(max=50, message="Password cannot be longer than 50 characters"),
                            Required(message='Password is required')])
    submit = SubmitField("submit")

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        rv = Form.validate(self)
        num_errors = 0
        if not rv:
            num_errors = num_errors + 1

        if not User.is_email_available(self.email.data):
            self.email.errors.append('This email has been registered. Try a different one')
            num_errors = num_errors + 1

        if not User.is_username_available(self.username.data):
            self.username.errors.append('This username has been registered. Try a different one')
            num_errors = num_errors + 1

        if num_errors > 0:
            return False

        return True
