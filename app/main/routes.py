from app.main import bp
from app import db
from flask import render_template, request
from app.models import Category, Products, Price, Balance, Cart
import json
from flask_login import current_user


from flask import g
from app.main.forms import SearchForm

@bp.before_app_request
def before_request():
    g.search_form = SearchForm()


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    cat = Category.query.filter_by(parent_id=None).all()
    sub_cat = Category.query.filter_by(level=2).order_by(db.desc(Category.level)).all()
    sub_cat_2 = Category.query.filter_by(level=3).order_by(db.desc(Category.level)).all()


    category_level_one = {}
    category_level_two = {}
    category_list_level_three = []

    for c in cat:
        category_level_one[c.name] = {}
        for s in sub_cat:
            if s.parent_id != c.id_category:
                continue
            category_level_two[s.name] = []
            for s2 in sub_cat_2:
                if s2.parent_id != s.id_category:
                    continue
                category_list_level_three.append(s2.name)
            category_level_two[s.name] = category_list_level_three
            category_list_level_three = []
        category_level_one[c.name] = category_level_two
        category_level_two = {}

    clothes_count = 0
    if current_user.is_authenticated:
        clothes_count = db.session.query(Cart).filter_by(user_id=current_user.get_id()).count()
    elif current_user.is_anonymous:
        if request.cookies.get('cart'):
            res = request.cookies.get('cart')
            article_size_cart = json.loads(res.replace("'", '"'))
            clothes_count = str(len(article_size_cart))





    return render_template('main/index.html', category=category_level_one, enumerate=enumerate, clothes_count=clothes_count)