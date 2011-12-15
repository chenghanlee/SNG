from flask import abort, Blueprint, jsonify, render_template,\
                  request, session
from flask.ext.login import current_user, login_required
from werkzeug import Href, url_fix

from helppme.helper import get_current_user, get_deal, \
                           insert_new_deal_into_list, remove_deal,\
                           remove_deal_num_from_lists, store_deal,\
                           store_list_of_deals, set_user_action_as_completed
from helppme.globals import affiliate_tag, categories, date_ranges,\
                            max_num_documents, per_page, r,\
                            short_title_length, sorts
from helppme.forms.forms import Deal_Form, Edit_Form
from helppme.models.deal import Deal
from helppme.models.user import User

from datetime import datetime

import helppme.celery_tasks as celery_tasks
import string

deals = Blueprint('deals', __name__)


@deals.route('/deals/404/', methods=['GET'])
def show_404():
    abort(404)


@deals.route('/deals/<int:sequence_num>/<short_title>/', methods=['GET'])
def show_deal(sequence_num, short_title):
    deal_json = get_deal(sequence_num)
    if deal_json is None:
        deal = Deal.objects(sequence_num=sequence_num,
                            short_title=short_title).first()
        if deal == None:
            abort(404)
        deal_json = jsonify(deal)

    # current date and sort are needed to build the url in the category and
    # date filter sidebar
    current_date = session.get('current_date', 'week')
    current_sort = session.get('current_sort', 'trending')
    return render_template('deal.html', deal=deal_json,
                            current_category=deal_json['category'],
                            current_date=current_date,
                            current_sort=current_sort)


@deals.route('/deals/<deal_id>/edit/', methods=['POST'])
def edit_deal(deal_id):
    '''
    This function is used to allow a user to edit the description of a deal
    that he or she has submitted
    '''
    deal = Deal.objects(id=deal_id).first()
    if deal is None:
        return abort(404)
    user = get_current_user()
    if user is None or str(get_current_user().id) != deal.author_id:
        return abort(404)

    msg = {}
    form = Edit_Form(csrf_enabled=False)
    if request.method == 'POST' and form.validate_on_submit():
        print request.form
        description = request.form.get('description', None)
        if description:
            deal.description = description
            deal.edited = datetime.now()
            deal.save()
            store_deal(deal, overwrite=True)
        next = Href('/')
        next = next('deals', deal.sequence_num, deal.short_title)
        msg['status'] = 'success'
    else:
        msg['status'] = 'error'
        msg['description_error'] = form.description.errors[0]
    return jsonify(msg)


@deals.route('/deals/<deal_id>/url/', methods=['GET'])
def get_url(deal_id):
    deal = Deal.objects(id=deal_id).first()
    url_root = request.url_root
    url = "".join([url_root, deal.url[1:]])  # strips the leading "/"
    msg = {'url': url}
    return jsonify(msg)


@deals.route('/deals/post/', methods=['GET', 'POST'])
@login_required
def post_deal():
    form = Deal_Form()
    # if current_user is None:
    #     msg = {"status": "error", "message": "user not logged in"}
    #     return msg
    if request.method == 'GET':
        return render_template('post_deal.html', form=form)
    elif request.method == 'POST':
        if form.validate_on_submit():
            title = request.form.get('title')
            title = string.strip(title)
            short_title = title[0:short_title_length - 1]
            short_title = string_to_url_fix(short_title)
            category = request.form.get('categories')
            category = string.lower(category)
            location = request.form.get('location', None)
            if location == "":
                location = None
            if location and is_amazon_url(location):
                location = gen_amazon_affiliate_url(location)
            description = request.form.get('description', None)
            user = get_current_user()
            ip = request.remote_addr
            new_deal = Deal(title=title, short_title=short_title,
                            location=location, category=category,
                            description=description, author_id=str(user.id),
                            num_votes=1, ip=ip)
            new_deal.save()

            new_deal_id = new_deal.id
            # updating redis cache
            store_deal(new_deal)
            insert_new_deal_into_list(category, new_deal.sequence_num)
            set_user_action_as_completed('vote', new_deal_id, user.sequence_num)
            for sort in sorts:
                r.delete("".join([user.name, '_', 'shared', '_', sort]))
            # updating mongodb or datastore
            user.deals_voted.append(str(new_deal_id))
            user.deals_submitted.append(str(new_deal_id))
            user.save()
            celery_tasks.upvote.delay(new_deal_id, user.id, request.remote_addr)

            #building this deal's url so to redirect the user
            next = Href('/')
            next = next('deals', new_deal.sequence_num, new_deal.short_title)
            msg = {'status': 'success', 'redirect': next}
            return jsonify(msg)
        else:
            #if form returns errors, return the errors to the users via js
            msg = {"status": "error"}
            if form.title.errors:
                msg["title_error"] = form.title.errors[0]
            if form.location.errors:
                msg["location_error"] = form.location.errors[0]
            if form.categories.errors:
                msg["category_error"] = form.categories.errors[0]
            if form.description.errors:
                msg["description_error"] = form.description.errors[0]
            return jsonify(msg)
    else:
        abort(404)


@deals.route('/deals/do_action/', methods=['POST'])
def do_action():
    '''
    This function is called by custom.js to complete various action on a deal.
    It first checks the validity of the user and the input. Namely, is the
    user logged in, is the deal id passed in, is the deal_id valid.
    It returns appropriate error msg if the above conditions are not met.

    If the conditions are met, this functions calls other helper functions
    to complete actions as requested by custom.js, such as upvote, save, flag
    and delete.
    '''
    deal_id = request.form.get('deal_id', None)
    action = request.form.get('action', None)

    #error checking below:
    #user is not logged in
    msg = {}
    if current_user.is_anonymous():
        msg['status'] = 'error'
        msg['message'] = 'user not logged in'
        return jsonify(msg)
    #deal_id is not passed in
    if deal_id is None:
        msg['status'] = 'error'
        msg['message'] = 'deal id not passed in'
        return jsonify(msg)
    #we cannot find a deal with the deal id that's passed in
    deal_queryset = Deal.objects(id=deal_id)
    if deal_queryset.first() is None:
        msg['status'] = 'error'
        msg['message'] = 'deal does not exist'
        return jsonify(msg)

    #call helper tasks to complete the action
    if action == 'vote':
        msg = vote_deal(deal_id)
    elif action == 'save':
        msg = save_deal(deal_id)
    elif action == 'flag':
        msg = flag_deal(deal_id)
    elif action == 'delete':
        msg = delete_deal(deal_id)
    return msg


@deals.route('/', defaults={'category': 'everything', 'page': 1,
                            'date_range': 'week', 'sort': 'trending'},
                  methods=['GET'])
# @deals.route('/deals/', defaults={'category': 'everything', 'page': 1,
#                                   'date_range': 'week', 'sort': 'trending'},
#                         methods=['GET'])
@deals.route('/deals/<category>/', defaults={'page': 1, 'date_range': 'week',
                                             'sort': 'trending'},
                                   methods=['GET'])
@deals.route('/deals/<category>/<date_range>/', defaults={'page': 1,
                                                          'sort': 'trending'},
                                                methods=['GET'])
@deals.route('/deals/<category>/<date_range>/<sort>/', defaults={'page': 1},
                                                       methods=['GET'])
@deals.route('/deals/<category>/<date_range>/<sort>/<int:page>/',
             methods=['GET'])
def show_homepage(category, date_range, sort, page):
    '''
    This method returns a liste of deals as filtered and sorted by
    category, date_range, and sort. The list of deals is then paginated
    which allows us to display deals per page in the template view.
    '''
    #sanity check: making sure the input values are valid
    if page < 1 or category not in categories or sort not in sorts or \
       date_range not in date_ranges:
        abort(404)

    #checking to see if the requestesd deal data is stored in redis
    key = [category, '_', date_range, '_', sort]
    key = ''.join(key)
    deal_seq_nums = None
    if r.exists(key):
        deal_seq_nums = r.lrange(key, 0, -1)
        if deal_seq_nums == ['None']:
            deal_seq_nums = []
    else:
        deal_queryset = query_for_deals(category, date_range, sort)
        deal_seq_nums = [deal.sequence_num for deal in deal_queryset]
        store_list_of_deals(key, deal_seq_nums)
        # for deal in deal_queryset:
        #     store_deal(deal)

    #preparing some date to pass into the template
    start = (page - 1) * per_page
    end = page * per_page
    has_next = True if end < len(deal_seq_nums) else False
    has_previous = True if start > 0 else False
    deal_seq_nums = deal_seq_nums[start:end]

    # remembering  current_date, and current_sort in session
    # this is useful when a user's in a specific deal's page and we need
    # to highlight the correct sidebar filter links
    session['current_date'] = date_range
    session['current_sort'] = sort

    return render_template('homepage.html', current_category=category,
                           current_date=date_range, current_sort=sort,
                           current_page=page, deal_seq_nums=deal_seq_nums,
                           has_next=has_next, has_previous=has_previous,
                           next_page=page + 1, previous_page=page - 1)

'''
Helper functions:
    These functions do not listen for URL requests. They are used as helper
    functions by functions with @route decorators
'''


def query_for_deals(category, date_range, sort):
    '''
    This function queries MongoDB according to the parameters. The retrieved
    documents will be filtered by category and date, then sorted by sort.
    '''
    from datetime import datetime, timedelta
    # The following is to account for the possiblity that the parameter
    # 'category' is equal to 'everything'. If that's case, we need to retrieve
    # any deal whose category is found in the global list, 'categories'

    # In order to create this kind of query, we need to use the keyword 'in'
    # rather than the traditional keyword '='. And queries using
    # 'in' requires us to query against a list of values rather than one
    # specific value
    categories_to_query_against = []
    if category == 'everything':
        # excluding the catch-all-category "everything"
        categories_to_query_against = categories[1:]
    else:
        categories_to_query_against = [category]

    #filter the documents by category and date
    date_ranges = {
        'today': datetime.now() - timedelta(days=1),
        'week': datetime.now() - timedelta(days=7),
        'month': datetime.now() - timedelta(days=30),
        'year': datetime.now() - timedelta(days=356),
    }
    min_date = date_ranges[date_range]
    type_of_sorts = {'newest': '-created', 'popular': '-num_votes', 'trending': '-score'}
    sort = type_of_sorts.get(sort, '-created')
    deals = Deal.objects(created__gte=min_date,
                         category__in=categories_to_query_against,
                         dead=False,
                         deleted=False) \
                         .order_by(sort) \
                         .limit(max_num_documents) \
                         .exclude('flags', 'sockvotes', 'votes')
    return deals

'''
The following 4 functions, vote, save, flag, and delete are used in
conjunction with javascript to provide ajax functionalities for a user
when the user votes, saves, flags, or deletes a deal
'''


def delete_deal(deal_id):
    '''
    This function is used by a user to delete a deal. The user trying to
    delete this deal must be the author of the deal.

    We are not sending this off to celery as a async task b'c we want to
    ensure that this a deal is deleted immediately, rather at time delta
    later
    '''
    msg = {}
    user = User.objects(id=current_user.id).first()
    if str(deal_id) not in user.deals_submitted:
        msg['status'] = 'error'
        msg['message'] = 'you cannot delete this deal b\'c you are not the author'
        return jsonify(msg)
    try:
        deal = Deal.objects(id=deal_id).first()
        deal.deleted = True
        deal.save()
        remove_deal(deal.sequence_num)
        remove_deal_num_from_lists(deal.sequence_num)
    except Exception as e:
        print e
        msg['status'] = 'error'
        msg['message'] = 'error occured while deleting user object'
        return jsonify(msg)

    msg['status'] = 'success'
    return jsonify(msg)


def flag_deal(deal_id):
    '''
    This function is used by a user to flag a deal as inappropriate or spam
    '''
    msg = {}
    user = get_current_user()
    if str(deal_id) in user.deals_flagged:
        msg['status'] = 'error'
        msg['message'] = 'you cannot flag the same deal twice'
    else:
        user.deals_flagged.append(deal_id)
        user.save()
        celery_tasks.flag.delay(deal_id, user.id)
        # noting that current user has flagged this deal
        set_user_action_as_completed('flag', deal_id, user.sequence_num)
        msg['status'] = 'success'
    return jsonify(msg)


def save_deal(deal_id):
    '''
    This allows a user to bookmark a deal, so the user can refer to the deal
    at a later time
    '''
    msg = {}
    user = get_current_user()
    if str(deal_id) in user.deals_saved:
        msg['status'] = 'error'
        msg['message'] = 'you cannot save the same deal twice'
    else:
        user.deals_saved.append(deal_id)
        user.save()
        # noting that current user has bookmarked this deal
        set_user_action_as_completed('save', deal_id, user.sequence_num)
        # updating our redis cache
        for sort in sorts:
            r.delete("".join([user.name, '_', 'bookmarked', '_', sort]))
        msg['status'] = 'success'
    return jsonify(msg)


def vote_deal(deal_id):
    '''
    This function updates the number of votes of the deal by:
        1) increasing num_votes by 1
        2) add a new vote object into a deal's 'votes' list
    '''
    msg = {}
    user = get_current_user()
    if str(deal_id) in user.votes:
        msg['status'] = 'error'
        msg['message'] = 'you cannot vote for the same deal twice'
        return jsonify(msg)

    # we want to make sure that the user see's that his or her vote was counted
    # right away w/o any delay. Hence, the following line is part of
    # celery_tasks.upvote
    else:
        try:
            user.deals_voted.append(str(deal_id))
            user.save()
            deal_queryset = Deal.objects(id=deal_id)
            deal_queryset.update_one(inc__num_votes=1)
            deal = deal_queryset.first()
            # flushing redis cache to reflect the new vote count
            remove_deal(deal.sequence_num)
            # update redis cache: noting that current user has voted this deal in redis
            set_user_action_as_completed('vote', deal_id, user.sequence_num)
            for sort in sorts:
                r.delete("".join([user.name, '_', 'liked', '_', sort]))
            # update mongodb
            celery_tasks.upvote.delay(deal_id, user.id, request.remote_addr)
            msg['status'] = 'success'
            return jsonify(msg)
        except Exception as e:
            print e
            abort(404)

#these are functions to determine if an url is an amazon url and
#convert the url to include our amazon affiliate url if needed


def is_amazon_url(url):
    if string.find(url, 'www.amazon') > -1:
        return True
    return False


def gen_amazon_affiliate_url(url):
    if string.find(url, '/dp/') >= 0:
        asin_length = 10
        dp_offset = 4
        start = string.find(url, '/dp/') + dp_offset
        end = start + asin_length
        url = url[:end]
        url = "".join([url, affiliate_tag])
        return url
    else:
        url = "".join([url, affiliate_tag])
        return url


def string_to_url_fix(some_string):
    '''
    This method converts a string to into another string that can be safely
    used as an URL. This is done by removing any characters that is not a
    letter or a digit. Also, all white spaces are converted to a dash.
    '''

    modified_string = [c for c in some_string \
                       if c in string.ascii_letters \
                       or c in string.digits \
                       or c == ' ']
    modified_string = string.replace(''.join(modified_string), ' ', '-')
    #in case any non-URL safe characters sneaks into some_string
    modified_string = url_fix(modified_string)

    return modified_string
