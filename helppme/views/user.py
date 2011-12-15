from flask import abort, Blueprint, jsonify, redirect, render_template, \
                  request, session
from flask.ext.login import login_user, logout_user

from helppme.helper import get_current_user, store_list_of_deals, store_deal
from helppme.globals import max_num_documents, per_page, r, signer, sorts,\
                            user_history_filters
from helppme.forms.forms import Login_Form, Signup_Form, Password_Reset_Form,\
                                Password_Request_Form
from helppme.models.deal import Deal
from helppme.models.user import User

user = Blueprint('user', __name__)


@user.route('/user/signup', methods=['POST'])
def signup():
    '''
    This creates an account for the user. This is used in adjunction with
    javascript to create an ajax signup form
    '''
    form = Signup_Form(csrf_enabled=False)

    if request.method == 'POST' and form.validate_on_submit():
        username = request.form.get('username', None)
        email = request.form.get('email', None)
        password = request.form.get('password', None)
        password_hash = User.gen_hash(password)
        new_user = User(name=username, email=email,
                        password_hash=password_hash)
        new_user.save()
        login_user(new_user)
        return jsonify(status="success", redirect=request.referrer)
    else:
        #we assume that there at most 1 error for any field
        errors = {}
        if len(form.email.errors) > 0:
            errors["email_error"] = form.email.errors[0]
        if len(form.username.errors) > 0:
            errors["username_error"] = form.username.errors[0]
        if len(form.password.errors) > 0:
            errors["password_error"] = form.password.errors[0]
        if errors:
            errors["status"] = "error"
        return jsonify(errors)


@user.route('/user/login', methods=['POST'])
def login():
    form = Login_Form(csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        login_user(form.user)
        next = session.pop('next', None)
        if next is not None:
            return jsonify(status="success", redirect=next)
        else:
            return jsonify(status="success", redirect=request.referrer)
    else:
        return jsonify(status="error", msg="Wrong username or password")


@user.route('/user/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    return redirect(request.referrer)


@user.route('/user/password_reset/', methods=["GET", "POST"])
def reset_password():
    token = request.args.get('token', None)
    if token is None:
        abort(404)

    name = None
    try:
        # token must be < 2 days (or 172800 seconds) old
        name = signer.loads(token, max_age=172800)
    except Exception as e:
        abort(404)
    user = User.objects(name=name).first()
    if user is None:
        abort(404)

    form = Password_Reset_Form()
    if request.method == "POST" and form.validate_on_submit():
        new_password = request.form.get('password')
        user.change_password(new_password)
        return redirect('change_password_success.html')
    else:
        return render_template('change_password.html', form=form)


@user.route('/user/forgot_password/', methods=["POST"])
def forgot_password():
    form = Password_Request_Form(csrf_enabled=False)
    msg = {}
    if request.method == "POST" and form.validate_on_submit():
        username = request.form.get('username')
        user = User.objects(name=username)
        if user is not None:
            token = signer.dumps(username)
            # gen_passwod_reset_email(user.email, token)
        msg['status'] = "success"
    else:
        msg['status'] = "error"
        msg['email_error'] = form.email.errors[0]
    return jsonify(msg)


@user.route('/user/<name>/', defaults={'filter_by': 'shared', 'page': 1, 'sort': 'newest'}, methods=['GET'])
@user.route('/user/<name>/<filter_by>/', defaults={'page': 1, 'sort': 'newest'}, methods=['GET'])
@user.route('/user/<name>/<filter_by>/<sort>/', defaults={'page': 1}, methods=['GET'])
@user.route('/user/<name>/<filter_by>/<sort>/<int:page>', methods=['GET'])
def show_user_profile(name, filter_by, page, sort):
    '''
    This method retrieve a list of deals shared or bookmarked by the
    user. This method is used to show the user's history on the site.

    A user's bookmark is private to the user's eye's only. Abort 404 will be
    thrown if a users try to access some other user's bookmark.
    '''
    #sanity check our inputs
    if sort not in sorts:
        return abort(404)
    #are we trying to retrieve the profile of a non-existent user?
    page_owner = User.objects(name=name).first()
    if page_owner is None:
        return abort(404)
    # if we are trying filtering by the correct categories?
    if filter_by not in user_history_filters:
        return abort(404)
    #do not allow other users to see other user's bookmark
    current_user = get_current_user()
    if filter_by == 'bookmarked' and (current_user == None or
                                     current_user.name != name):
        return abort(404)
    key = [name, '_', filter_by, '_', sort]
    key = ''.join(key)
    deal_seq_nums = None
    if r.exists(key):
        deal_seq_nums = r.lrange(key, 0, -1)
        if deal_seq_nums == ['None']:
            deal_seq_nums = []
    else:
        deal_queryset = query_for_deals(page_owner, filter_by, sort)
        deal_seq_nums = [deal.sequence_num for deal in deal_queryset]
        store_list_of_deals(key, deal_seq_nums)
        for deal in deal_queryset:
            store_deal(deal)

    start = (page - 1) * per_page
    end = page * per_page
    has_next = True if end < len(deal_seq_nums) else False
    has_previous = True if start > 0 else False
    deal_seq_nums = deal_seq_nums[start:end]
    return render_template('user_history.html', current_filter=filter_by,
                            current_page=page, current_sort=sort,
                            owner=page_owner, deal_seq_nums=deal_seq_nums,
                            has_next=has_next, has_previous=has_previous)

    # pagination = query_for_deals(user, filter_by).paginate(page=1, per_page=per_page)
    # return render_template('user_history.html', current_sort=sort, owner_name=name, pagination=pagination)

'''
helper functions below:
    These functions do not listen to a specific route. Rather, they are used
    by the functions above to complete some specific action
'''


def query_for_deals(user, filter_by, sort):
    '''
    This function takes the user and sort parameters and queries MongoDB
    accordingly. The retrieved documents will be filtered and sorted as
    defined by by the parameters user and sort.
    '''
    deals = None
    type_of_sorts = {'newest': '-created', 'popular': '-num_votes',
                     'trending': '-score'}
    sort = type_of_sorts.get(sort, '-created')
    if filter_by == 'shared':
        deals = Deal.objects(deleted=False,
                             author_id=str(user.id))\
                             .order_by(sort)\
                             .limit(max_num_documents)\
                             .exclude('flags', 'sockvotes', 'votes')
    elif filter_by == 'liked':
        deals = Deal.objects(id__in=user.deals_voted)\
                             .order_by(sort)\
                             .limit(max_num_documents)\
                             .exclude('flags', 'sockvotes', 'votes')
    elif filter_by == 'bookmarked':
        deals = Deal.objects(id__in=user.deals_saved)\
                             .order_by(sort)\
                             .limit(max_num_documents)\
                             .exclude('flags', 'sockvotes', 'votes')
    else:
        return abort(404)
    return deals
