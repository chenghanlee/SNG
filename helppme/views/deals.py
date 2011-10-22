from flask import Blueprint, redirect, render_template, request, url_for
from flask.ext import login

from helppme.forms.forms import Item_Form
from helppme.models.item import Item

import string 

deals = Blueprint('deals', __name__)

@deals.route('/', methods=['GET', 'POST'])
def show_homepage():
	return render_template('homepage.html')

@deals.route('/post', methods=['GET', 'POST'])
def post_deal():
	form = Item_Form()

	if request.method == 'POST' and form.validate_on_submit():
		title = request.form.get('title', None)
		url = request.form.get('url', None)
		category = request.form.get('category', None)
		description = request.form.get('description', None)
		#user = get_current_user()
		ip = request.remote_addr
		#new_item = Item(title=title, url=url, category=category, 
		#				profile=user, ip=ip)
		new_item = Item(title=title, url=url, category=category,
						description=description, ip=ip)
		new_item.save()
		title=string.replace(title, ' ', '-')
		return redirect(url_for('.show_deal', 
								sequence_num=new_item.sequence_num, 
								title=title))
	else:
		return render_template('post_deal.html', form=form)

@deals.route('/deal/<deal_num>/<title>', methods=['GET'])
def show_deal(deal_num, title):
	title = string.replace(title, '-', ' ')
	item = Item.objects(sequence_num=deal_num, title=title).first()
	return render_template('deal.html', deal=item)


@deals.route('/deal', methods=['GET'])
def show_temp_deal():
	return render_template('deal.html')	