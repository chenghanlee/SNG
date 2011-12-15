from flask import Blueprint, render_template, request, session

other = Blueprint('other', __name__)


@other.route('/login_required/')
def login_required():
    next_page = request.args.get('next', 'nothing here')
    session['next'] = next_page
    return render_template('login_required.html')


@other.route('/terms/', methods=['GET'])
def show_terms():
    return render_template('terms.html')


@other.route('/privacy/', methods=['GET'])
def show_privacy():
    return render_template('privacy.html')
