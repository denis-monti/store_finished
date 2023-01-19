
from app.catalog import bp
from flask import render_template, flash, redirect, url_for, request, render_template_string, g, \
    jsonify, current_app, session, make_response, abort
from flask_login import current_user, login_required
from app.models import Category, Products, Price, Balance, Review, Path_picture, User, Review_liking_check, Cart

from werkzeug.utils import secure_filename
from app import db

import os

from sqlalchemy.sql import func, and_, or_, not_, case, null, alias, distinct

import json

from app.catalog.forms import *

from flask_paginate import Pagination


@bp.route('/search_ajax/', methods=['GET', 'POST'])
def search_ajax():
    if current_user.is_authenticated:
        clothes_count = db.session.query(Cart).filter_by(user_id=current_user.get_id()).count()
    elif current_user.is_anonymous:
        if request.cookies.get('cart'):
            res = request.cookies.get('cart')
            article_size_cart = json.loads(res.replace("'", '"'))
            clothes_count = str(len(article_size_cart))
        else:
            clothes_count = str(0)
    filter_brand = request.form['filter_value_brand']
    filter_color = request.form['filter_value_color']
    filter_size = request.form['filter_value_size']
    target_form = request.form['target_form']
    min_price = request.form['min_price']
    max_price = request.form['max_price']
    ids_raw = request.form['ids']
    type_chapter = request.form['type_chapter']
    form_filter = SimpleForm()
    idss = [n.strip() for n in ids_raw.split(sep=',')]
    filter_brand = [n.strip() for n in filter_brand.split(sep=',')]
    filter_color = [n.strip() for n in filter_color.split(sep=',')]
    filter_size = [n.strip() for n in filter_size.split(sep=',')]


    if type_chapter == 'search':
        form_filter.brand.choices = db.session.query(Products.brand, func.count(Products.brand)).filter(
            (Products.id_Product.in_(idss))).group_by(Products.brand).all()
        form_filter.color.choices = db.session.query(Products.color, func.count(Products.color)).filter(
            (Products.id_Product.in_(idss))).group_by(Products.color).all()

        form_filter.size.choices = db.session.query(Balance.size, func.sum(case([(Balance.count >= 1, 1)], else_=0)).label(
            'count_size')).join(Products, (Balance.product_article_balance == Products.product_article) & (
                Products.id_Product.in_(idss))).group_by(Balance.size).all()



        if filter_brand == ['']:
            filter_default = db.session.query(Products.brand).filter(Products.id_Product.in_(idss)).group_by(Products.brand).all()
            filter_brand.append('default')
            for i in filter_default:
                filter_brand.append(i[0])
        if filter_color == ['']:
            filter_default = db.session.query(Products.color).filter(Products.id_Product.in_(idss)).group_by(
                Products.color).all()
            filter_color.append('default')
            for i in filter_default:
                filter_color.append(i[0])
        if filter_size == ['']:
            filter_default = db.session.query(Balance.size).join(Products, (Balance.product_article_balance == Products.product_article) & (Products.id_Product.in_(idss))).group_by(
                Balance.size).all()
            filter_size.append('default')
            for i in filter_default:
                filter_size.append(i[0])


        minimum_maximum_price_default = db.session.query(func.min(Price.current_price), func.max(Price.current_price)) \
            .join(Products, Price.product_article_price == Products.product_article).filter(
            Products.id_Product.in_(idss)).first()
        if target_form == 'price':
            all_filter = db.session.query(Products.brand, Products.color, Products.product_article, Balance.size, Balance.count) \
                .join(Balance, Products.product_article == Balance.product_article_balance).join(Price, Products.product_article == Price.product_article_price).filter(
                (Products.brand.in_(filter_brand)) & (Products.color.in_(filter_color))
                & (Balance.size.in_(filter_size)) & (Products.id_Product.in_(idss)) & (Price.current_price.between(min_price, max_price))).subquery()
        else:
            all_filter = db.session.query(Products.brand, Products.color, Products.product_article, Balance.size,
                                          Balance.count) \
                .join(Balance, Products.product_article == Balance.product_article_balance).filter(
                (Products.brand.in_(filter_brand)) & (Products.color.in_(filter_color))
                & (Balance.size.in_(filter_size)) & (Products.id_Product.in_(idss)) ).subquery()
    elif type_chapter == 'catalog':
        form_filter.brand.choices = db.session.query(Products.brand, func.count(Products.brand)).filter(
            (Products.category_product.in_(idss))).group_by(Products.brand).all()
        form_filter.color.choices = db.session.query(Products.color, func.count(Products.color)).filter(
            (Products.category_product.in_(idss))).group_by(Products.color).all()
        form_filter.size.choices = db.session.query(Balance.size,
                    func.sum(case([(Balance.count >= 1, 1)], else_=0)).label('count_size')).join(Products, (
                    Balance.product_article_balance == Products.product_article) & (Products.category_product.in_(
                    idss))).group_by(Balance.size).all()

        if filter_brand == ['']:
            filter_default = db.session.query(Products.brand).filter(Products.category_product.in_(idss)).group_by(
                Products.brand).all()
            filter_brand.append('default')
            for i in filter_default:
                filter_brand.append(i[0])
        if filter_color == ['']:
            filter_default = db.session.query(Products.color).filter(Products.category_product.in_(idss)).group_by(
                Products.color).all()
            filter_color.append('default')
            for i in filter_default:
                filter_color.append(i[0])
        if filter_size == ['']:
            filter_default = db.session.query(Balance.size).join(Products, (
                        Balance.product_article_balance == Products.product_article) & (
                                                                     Products.category_product.in_(idss))).group_by(
                Balance.size).all()
            filter_size.append('default')
            for i in filter_default:
                filter_size.append(i[0])

        minimum_maximum_price_default = db.session.query(func.min(Price.current_price), func.max(Price.current_price)) \
            .join(Products, Price.product_article_price == Products.product_article).filter(
            Products.category_product.in_(idss)).first()
        if target_form == 'price':
            all_filter = db.session.query(Products.brand, Products.color, Products.product_article, Balance.size, Balance.count) \
                .join(Balance, Products.product_article == Balance.product_article_balance)\
                .join(Price, Products.product_article == Price.product_article_price).filter(
                (Products.brand.in_(filter_brand)) & (Products.color.in_(filter_color))
                & (Balance.size.in_(filter_size)) & (Products.category_product.in_(idss)) & (
                    Price.current_price.between(min_price, max_price))).subquery()
        else:
            all_filter = db.session.query(Products.brand, Products.color, Products.product_article, Balance.size,
                                          Balance.count) \
                .join(Balance, Products.product_article == Balance.product_article_balance).filter(
                (Products.brand.in_(filter_brand)) & (Products.color.in_(filter_color))
                & (Balance.size.in_(filter_size)) & (Products.category_product.in_(idss))).subquery()



    enabled_brand = db.session.query(Products.brand, func.count(distinct(all_filter.c.product_article))) \
        .join(all_filter, (Products.brand == all_filter.c.brand) & (
            Products.product_article == all_filter.c.product_article) & (all_filter.c.count != 0)) \
        .group_by(Products.brand).all()

    enabled_color = db.session.query(Products.color, func.count(distinct(all_filter.c.product_article))).join(
        all_filter, (
                            Products.color == all_filter.c.color) & (
                            Products.product_article == all_filter.c.product_article) & (
                            all_filter.c.count != 0)).group_by(
        Products.color).all()

    enabled_size = db.session.query(Balance.size, func.sum(case([(Balance.count >= 1, 1)], else_=0))).join(
        all_filter, (
                            Balance.size == all_filter.c.size) & (
                            Balance.product_article_balance == all_filter.c.product_article)).group_by(
        Balance.size).all()



    if target_form == 'price':
        if min_price == '':
            minimum_maximum_price = [minimum_maximum_price_default[0], int(max_price)]
        elif max_price == '':
            minimum_maximum_price = [int(min_price), minimum_maximum_price_default[1]]
        elif min_price == '' and max_price == '':
            minimum_maximum_price = [minimum_maximum_price_default[0], minimum_maximum_price_default[1]]
        else:
            minimum_maximum_price = [int(min_price), int(max_price)]

    else:
        minimum_maximum_price = db.session.query(func.min(Price.current_price), func.max(Price.current_price)) \
            .join(all_filter, (
                Price.product_article_price == all_filter.c.product_article)).first()


    if minimum_maximum_price[0] == minimum_maximum_price_default[0] and minimum_maximum_price[1] == minimum_maximum_price_default[1] :
        price_active = False
    else :
        price_active = True
    if type_chapter == 'search':
        return render_template('catalog/ajax_filter_for_search.html', price_active=price_active, form=form_filter, minimum_price=json.dumps(minimum_maximum_price[0]), maximum_price=json.dumps(minimum_maximum_price[1]),
                               enabled_size=enabled_size, enabled_color=enabled_color, enabled_brand=enabled_brand, default_minimum_price=json.dumps(minimum_maximum_price_default[0]), default_maximum_price=json.dumps(minimum_maximum_price_default[1]),
                               enumerate=enumerate, sum_id_clothes=ids_raw, filter_brand=filter_brand, filter_color=filter_color, filter_size=filter_size, target_form=target_form, clothes_count=clothes_count, type_chapter=type_chapter)
    elif type_chapter == 'catalog':
        return render_template('catalog/ajax_filter_for_search.html', price_active=price_active, form=form_filter,
                               minimum_price=json.dumps(minimum_maximum_price[0]),
                               maximum_price=json.dumps(minimum_maximum_price[1]),
                               enabled_size=enabled_size, enabled_color=enabled_color, enabled_brand=enabled_brand,
                               default_minimum_price=json.dumps(minimum_maximum_price_default[0]),
                               default_maximum_price=json.dumps(minimum_maximum_price_default[1]),
                               enumerate=enumerate, sum_id_clothes=ids_raw, filter_brand=filter_brand,
                               filter_color=filter_color, filter_size=filter_size, target_form=target_form,
                               clothes_count=clothes_count, type_chapter=type_chapter)


@bp.route('/search/', methods=['GET', 'POST'])
def search():
    if current_user.is_authenticated:
        clothes_count = db.session.query(Cart).filter_by(user_id=current_user.get_id()).count()
    elif current_user.is_anonymous:
        if request.cookies.get('cart'):
            res = request.cookies.get('cart')
            article_size_cart = json.loads(res.replace("'", '"'))
            clothes_count = str(len(article_size_cart))
    form_sort = SortForm()
    form_filter = SimpleForm()

    filter_brand = []
    filter_color = []
    filter_size = []


    page = request.args.get('page', 1, type=int)
    total, sum_clothes = Products.search(g.search_form.q.data, page)

    if request.method == 'POST':
        search_data = g.search_form.q.data
        if form_filter.cancel.data == True:
            session.pop('sort_search', None)# удаление данных сортировки
            session.pop('filter_search', None)# удаление данных фильтра
        else:
            if form_sort.sort.data != None:
                session['sort_search'] = form_sort.sort.data

            minimum_maximum_price_default = db.session.query(func.min(Price.current_price),
                                                             func.max(Price.current_price)) \
                .join(Products, Price.product_article_price == Products.product_article).filter(
                Products.id_Product.in_(sum_clothes)).first()
            # Дописать условие для первого захода на страницу запроса будет Get хотя сюда он и так не попадёт )
            if form_filter.brand.data != [] or form_filter.color.data != [] or form_filter.size.data != [] or form_filter.minprice.data != '' and form_filter.maxprice.data != '':
                if form_filter.minprice != minimum_maximum_price_default[0] and form_filter.maxprice != minimum_maximum_price_default[1]:
                    session['filter_search'] = form_filter.data
        return redirect(url_for('catalog.search', q=search_data))
    elif request.method == 'GET':
        if session.get('filter_search') != None:
            data = session.get('filter_search')
            for y, i in data.items():
                    if y == 'brand':
                        if i == []:
                            filter_default = db.session.query(Products.brand).filter(
                                Products.id_Product.in_(sum_clothes)).group_by(Products.brand).all()
                            filter_brand.append('default')
                            for i in filter_default:
                                filter_brand.append(i[0])
                        else:
                            filter_brand.append(i)
                            form_filter.brand.data = i
                    elif y == 'color':
                        if i == []:
                            filter_default = db.session.query(Products.color).filter(
                                Products.id_Product.in_(sum_clothes)).group_by(
                                Products.color).all()
                            filter_color.append('default')
                            for i in filter_default:
                                filter_color.append(i[0])
                        else:
                            filter_color.append(i)
                            form_filter.color.data = i
                    elif y == 'size':
                        if i == []:
                            filter_default = db.session.query(Balance.size).join(Products, (
                                        Balance.product_article_balance == Products.product_article) & (
                                        Products.id_Product.in_(sum_clothes))).group_by(
                                Balance.size).all()
                            filter_size.append('default')
                            for i in filter_default:
                                filter_size.append(i[0])
                        else:
                            filter_size.append(i)
                            form_filter.size.data = i
                    elif y == 'minprice':
                        if i != '':
                            minimum_price = int(i)
                    elif y == 'maxprice':
                        if i != '':
                            maximum_price = int(i)
        if session.get('sort_search') != None and session.get('sort_search') != 'Default':
            sort_data = session.get('sort_search')
            form_sort.sort.data = sort_data


    if session.get('filter_search') == None:
        if total > 0:
            filter_clothes = False
            minimum_price = (((db.session.query(Price.current_price).join(Products,
                Price.product_article_price == Products.product_article)).filter(
                Products.id_Product.in_(sum_clothes))).order_by(Price.current_price).first()[0])
            maximum_price = (((db.session.query(Price.current_price).join(Products,
                Price.product_article_price == Products.product_article)).filter(
                Products.id_Product.in_(sum_clothes))).order_by(Price.current_price.desc()).first()[0])


            all_filter = db.session.query(Products.brand, Products.color, Products.product_article, Balance.size, Balance.count) \
                .join(Balance, Products.product_article == Balance.product_article_balance).join(Price,
                                                                                                 Products.product_article == Price.product_article_price).filter(
                 Products.id_Product.in_(sum_clothes)).subquery()
        else:
            filter_clothes = False
            minimum_price = 0
            maximum_price = 0
            all_filter = db.session.query(Products.brand, Products.color, Products.product_article, Balance.size, Balance.count) \
                .join(Balance, Products.product_article == Balance.product_article_balance).join(Price,
                Products.product_article == Price.product_article_price).filter((
                 Products.id_Product == 'False') & (Balance.count != 0)).subquery()
    else:
        filter_clothes = True
        all_filter = db.session.query(Products.brand, Products.color, Products.product_article, Balance.size,
                                      Balance.count) \
            .join(Balance, Products.product_article == Balance.product_article_balance).join(Price,
            Products.product_article == Price.product_article_price).filter(
            (Products.brand.in_(filter_brand)) & (Products.color.in_(filter_color))
            & (Balance.size.in_(filter_size)) & (Products.id_Product.in_(sum_clothes)) & (
                Price.current_price.between(minimum_price, maximum_price) & (Balance.count != 0))).subquery()

    enabled_brand = db.session.query(Products.brand, func.count(distinct(all_filter.c.product_article))) \
        .join(all_filter, (Products.brand == all_filter.c.brand) & (
            Products.product_article == all_filter.c.product_article) & (all_filter.c.count != 0)) \
        .group_by(Products.brand).all()

    enabled_color = db.session.query(Products.color, func.count(distinct(all_filter.c.product_article))).join(
        all_filter, (
                            Products.color == all_filter.c.color) & (
                            Products.product_article == all_filter.c.product_article) & (
                            all_filter.c.count != 0)).group_by(
        Products.color).all()

    enabled_size = db.session.query(Balance.size, func.sum(case([(Balance.count >= 1, 1)], else_=0))).join(
        all_filter, (
                            Balance.size == all_filter.c.size) & (
                            Balance.product_article_balance == all_filter.c.product_article)).group_by(
        Balance.size).all()

    minimum_maximum_price_default = db.session.query(func.min(Price.current_price), func.max(Price.current_price)) \
        .join(Products, Price.product_article_price == Products.product_article).filter(
        Products.id_Product.in_(sum_clothes)).first()



    if request.method == 'GET':
        clothes_default = db.session.query(Products, Price).join(Price, Products.product_article == Price.product_article_price).join(all_filter, Products.product_article == all_filter.c.product_article).group_by(Products.product_article)

        sort = session.get('sort_search')
        if sort == 'Price.max':
            clothes = clothes_default.order_by(Price.current_price)
        elif sort == 'Price.min':
            clothes = clothes_default.order_by(Price.current_price.desc())
        else:
            clothes = clothes_default
        pagination = Pagination(page=page, per_page=current_app.config['POSTS_PER_PAGE'],
                                display_msg="Displayed <span> {start} - {end} </span> of <span> {total} </span> of results",
                                total=int(clothes_default.count()), search=False, record_name='clothess')
        clothes = clothes.paginate(page, current_app.config['POSTS_PER_PAGE'], False)



    form_filter.brand.choices = db.session.query(Products.brand, func.count(Products.brand)).filter(
        (Products.id_Product.in_(sum_clothes))).group_by(Products.brand).all()
    form_filter.color.choices = db.session.query(Products.color, func.count(Products.color)).filter(
        (Products.id_Product.in_(sum_clothes))).group_by(Products.color).all()
    form_filter.size.choices = db.session.query(Balance.size, func.sum(case([(Balance.count >= 1, 1)], else_=0)).label('count_size')).join(Products,
        (Balance.product_article_balance == Products.product_article) & (Products.id_Product.in_(sum_clothes))
        ).group_by(Balance.size).all()

    return render_template('catalog/search.html', title='Search', sum_id_clothes=(str(sum_clothes))[1:-1], Clothes=clothes.items, pagination=pagination, clothes_count=clothes_count,
                           form=form_filter, form2=form_sort, minimum_price=json.dumps(minimum_price), maximum_price=json.dumps(maximum_price), filter_brand=filter_brand, default_minimum_price=json.dumps(minimum_maximum_price_default[0]), default_maximum_price=json.dumps(minimum_maximum_price_default[1]),
                           filter_color=filter_color, filter_size=filter_size, enumerate=enumerate, enabled_brand=enabled_brand, enabled_color=enabled_color, enabled_size=enabled_size, filter_clothes=filter_clothes)



@bp.route('/shop_sidebar/<name_category>/', methods=['GET', 'POST'])
def shope_sidebar(name_category):
    form_sort = SortForm()
    search_child_category = db.session.query(Category.name).filter(Category.parent_id.in_(db.session.query(Category.id_category).filter_by(parent_id=db.session.query(Category.id_category).filter_by(name=name_category))))

    page = request.args.get('page', 1, type=int)
    if request.method == 'GET':
        clothes_default = db.session.query(Products, Price).filter(Products.category_product.in_(search_child_category)).join(Price, Products.product_article == Price.product_article_price)
        sort = session.get('sort_catalog')
        if sort == 'Price.max':
            clothes = clothes_default.order_by(Price.current_price)
        elif sort == 'Price.min':
            clothes = clothes_default.order_by(Price.current_price.desc())
        else:
            clothes = clothes_default
        pagination = Pagination(page=page, per_page=current_app.config['POSTS_PER_PAGE'],
                                display_msg="Displayed <span> {start} - {end} </span> of <span> {total} </span> of results",
                                total=clothes.count(), search=False, record_name='clothess')
        clothes = clothes.paginate(page, current_app.config['POSTS_PER_PAGE'], False)



    if request.method == 'POST':
        if form_sort.sort.data != None:
            session['sort_catalog'] = form_sort.sort.data
        return redirect(url_for('catalog.shope_sidebar', name_category=name_category))
    elif request.method == 'GET':
        if session.get('sort_catalog') != None and session.get('sort_catalog') != 'Default':
            sort_data = session.get('sort_catalog')
            form_sort.sort.data = sort_data

            return render_template('catalog/shop-sidebar.html',  Clothes=clothes.items, enumerate=enumerate,  form2=form_sort, pagination=pagination, search=search_child_category.all())


    return render_template('catalog/shop-sidebar.html', Clothes=clothes.items, form2=form_sort, pagination=pagination, search=search_child_category.all())




    return render_template('catalog/shop-sidebar.html', Clothes=query_products, search=search_child_category.all())


@bp.route('/<name_category3>', methods=['GET', 'POST'])
def shope_sidebar_level_three(name_category3):
    if current_user.is_authenticated:
        clothes_count = db.session.query(Cart).filter_by(user_id=current_user.get_id()).count()
    elif current_user.is_anonymous:
        if request.cookies.get('cart'):
            res = request.cookies.get('cart')
            article_size_cart = json.loads(res.replace("'", '"'))
            clothes_count = str(len(article_size_cart))
        else:
            clothes_count = 0


    filter_brand = []
    filter_color = []
    filter_size = []
    name_filter = name_category3.replace('_', ' ')

    form_filter = SimpleForm()
    form_sort = SortForm()

    if request.method == 'POST':
        search_data = g.search_form.q.data
        if form_filter.cancel.data == True:
            session.pop('sort_catalog', None)# удаление данных сортировки
            session.pop('filter_catalog', None)# удаление данных фильтра
        else:
            if form_sort.sort.data != None:
                session['sort_catalog'] = form_sort.sort.data
            minimum_maximum_price_default = db.session.query(func.min(Price.current_price),
                                                             func.max(Price.current_price)) \
                .join(Products, Price.product_article_price == Products.product_article).filter(
                Products.category_product == name_filter).first()
            if form_filter.brand.data != [] or form_filter.color.data != [] or form_filter.size.data != [] or form_filter.minprice.data != '' and form_filter.maxprice.data != '':
                if form_filter.minprice != minimum_maximum_price_default[0] and form_filter.maxprice != minimum_maximum_price_default[1]:
                    session['filter_catalog'] = form_filter.data
        return redirect(url_for('catalog.shope_sidebar_level_three', name_category3=name_category3))
    elif request.method == 'GET':
        if session.get('filter_catalog') != None:
            data = session.get('filter_catalog')
            for y, i in data.items():
                    if y == 'brand':
                        if i == []:
                            filter_default = db.session.query(Products.brand).join(Category, Products.category_product == Category.name).filter(
                            (Category.name == name_filter)).group_by(Products.brand).all()
                            filter_brand.append('default')
                            for i in filter_default:
                                filter_brand.append(i[0])
                        else:
                            filter_brand.append(i)
                            form_filter.brand.data = i
                    elif y == 'color':
                        if i == []:
                            filter_default = db.session.query(Products.color).join(Category,
                            Products.category_product == Category.name).filter(
                            (Category.name == name_filter)).group_by(
                                Products.color).all()
                            filter_color.append('default')
                            for i in filter_default:
                                filter_color.append(i[0])
                        else:
                            filter_color.append(i)
                            form_filter.color.data = i
                    elif y == 'size':
                        if i == []:
                            filter_default = db.session.query(Balance.size).join(Products, (
                            Balance.product_article_balance == Products.product_article)).join(Category, Products.category_product == Category.name).filter(
                            (Category.name == name_filter)).group_by(
                                Balance.size).all()
                            filter_size.append('default')
                            for i in filter_default:
                                filter_size.append(i[0])
                        else:
                            filter_size.append(i)
                            form_filter.size.data = i
                    elif y == 'minprice':
                        if i != '':
                            minimum_price = int(i)
                    elif y == 'maxprice':
                        if i != '':
                            maximum_price = int(i)
        if session.get('sort_catalog') != None and session.get('sort_catalog') != 'Default':
            sort_data = session.get('sort_catalog')
            form_sort.sort.data = sort_data


    parent_cat = db.session.query(Category.name).filter(Category.id_category == (db.session.query(Category.parent_id).filter_by(id_category=db.session.query(Category.parent_id).filter_by(name=name_filter)))).all()

    form_filter.brand.choices = db.session.query(Products.brand, func.count(Products.brand)).filter(
        (Products.category_product == name_filter)).group_by(Products.brand).all()
    form_filter.color.choices = db.session.query(Products.color, func.count(Products.color)).filter(
        (Products.category_product == name_filter)).group_by(Products.color).all()
    form_filter.size.choices = db.session.query(Balance.size, func.sum(case([(Balance.count >= 1, 1)], else_=0)).label(
        'count_size')).join(Products, (Balance.product_article_balance == Products.product_article) & (
        Products.category_product == name_filter)).group_by(Balance.size).all()



    if session.get('filter_catalog') == None:
            filter_clothes = False
            all_filter = db.session.query(Products.brand, Products.color, Products.product_article, Balance.size, Balance.count) \
                .join(Balance, Products.product_article == Balance.product_article_balance).join(Price,
                 Products.product_article == Price.product_article_price)\
                .filter((Products.category_product == name_filter) & (Balance.count != 0)).subquery()
            minimum_price = (((db.session.query(Price.current_price).join(Products,
              Price.product_article_price == Products.product_article)).filter(
                ((Products.category_product == name_filter)))).order_by(Price.current_price).first()[0])


            maximum_price = (((db.session.query(Price.current_price).join(Products,
              Price.product_article_price == Products.product_article)).filter(
                (Products.category_product == name_filter))).order_by(Price.current_price.desc()).first()[0])

    else:
        filter_clothes = True
        all_filter = db.session.query(Products.brand, Products.color, Products.product_article, Balance.size,
                                      Balance.count) \
            .join(Balance, Products.product_article == Balance.product_article_balance).join(Price,
             Products.product_article == Price.product_article_price).filter(
            (Products.brand.in_(filter_brand)) & (Products.color.in_(filter_color))
            & (Balance.size.in_(filter_size)) & (Products.category_product == name_filter) & (
                Price.current_price.between(minimum_price, maximum_price)) & (Balance.count != 0)).subquery()





    enabled_brand = db.session.query(Products.brand, func.count(distinct(all_filter.c.product_article))) \
        .join(all_filter, (Products.brand == all_filter.c.brand) & (
            Products.product_article == all_filter.c.product_article) & (all_filter.c.count != 0)) \
        .group_by(Products.brand).all()

    enabled_color = db.session.query(Products.color, func.count(distinct(all_filter.c.product_article))).join(
        all_filter, (
                            Products.color == all_filter.c.color) & (
                            Products.product_article == all_filter.c.product_article) & (
                            all_filter.c.count != 0)).group_by(
        Products.color).all()

    enabled_size = db.session.query(Balance.size, func.sum(case([(Balance.count >= 1, 1)], else_=0))).join(
        all_filter, (
                            Balance.size == all_filter.c.size) & (
                            Balance.product_article_balance == all_filter.c.product_article)).group_by(
        Balance.size).all()

    minimum_maximum_price_default = db.session.query(func.min(Price.current_price), func.max(Price.current_price)) \
        .join(Products, Price.product_article_price == Products.product_article).join(all_filter, Price.product_article_price == all_filter.c.product_article).filter((
            Products.category_product == name_filter)& (Price.product_article_price == all_filter.c.product_article)).first()


    page = request.args.get('page', 1, type=int)
    if request.method == 'GET':
        clothes_default = db.session.query(Products, Price).join(Price,
         Products.product_article == Price.product_article_price).join(
            all_filter, Products.product_article == all_filter.c.product_article).group_by(Products.id_Product, Products.product_article, Price.id_balance)

        sort = session.get('sort_catalog')
        if sort == 'Price.max':
            clothes = clothes_default.order_by(Price.current_price)
        elif sort == 'Price.min':
            clothes = clothes_default.order_by(Price.current_price.desc())
        else:
            clothes = clothes_default
        pagination = Pagination(page=page, per_page=current_app.config['POSTS_PER_PAGE'],
                                display_msg="Displayed <span> {start} - {end} </span> of <span> {total} </span> of results",
                                total=clothes.count(), search=False, record_name='clothess')
        clothes = clothes.paginate(page, current_app.config['POSTS_PER_PAGE'], False)

    return render_template('catalog/shop-sidebar.html', Clothes=clothes.items, form=form_filter, enumerate=enumerate, name_category=name_filter,
                           minimum_price=json.dumps(minimum_price), maximum_price=json.dumps(maximum_price), default_minimum_price=json.dumps(minimum_maximum_price_default[0]),
                           default_maximum_price=json.dumps(minimum_maximum_price_default[1]), form2=form_sort, pagination=pagination, parent_cat=parent_cat,
                            filter_brand=filter_brand, filter_color=filter_color, filter_size=filter_size, clothes_count=clothes_count,
                            enabled_brand=enabled_brand, enabled_color=enabled_color, enabled_size=enabled_size, filter_clothes=filter_clothes)




@bp.route('/del/', methods=['GET', 'POST'])
def delete():
    session.pop('filter_search', None)
    session.pop('filter_catalog', None)
    session.pop('sort_search', None)
    session.pop('sort_catalog', None)
    session.pop('cart', None)
    resp = make_response()
    resp.delete_cookie('cart')
    return resp

import imghdr

def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return False
    elif format == 'jpeg':
        return True
    return '.' + format in current_app.config['UPLOAD_EXTENSIONS']


@bp.route('/product_details/<category>/<article>/', methods=['GET', 'POST'])
def product_details(article, category):
    form_message = ReviewForm()
    checking_review = (db.session.query(func.count(Review.user_id)).filter(
        (Review.user_id == current_user.get_id()) & (Review.article_product == article)).first()[0])
    if request.method == 'POST':
        if checking_review == 0:
            list_picture_path = ''
            for uploaded_file in request.files.getlist('file'):
                filename = secure_filename(uploaded_file.filename)
                if filename != '':
                    list_picture_path += current_app.config['SAVE_IMG_REVIEW_USER'] + filename + '\n'
                    if validate_image(uploaded_file.stream) == False:
                        return "Invalid image", 400
                    uploaded_file.save(os.path.join(current_app.config['UPLOAD_FOLDER_REVIEW'], filename))
            rating = request.form['rating']
            size = request.form['list_size_number']
            size_matching = request.form['list_size_matching']
            review = request.form['message']
            if list_picture_path != '':
                add_clothes = Review(user_id=current_user.get_id(), rating=rating, article_product=article,
                                     size_product=size,
                                   review=review, size_matching=size_matching, like=0, dislike=0)
                db.session.add(add_clothes)
                add_path = Path_picture(user_id=current_user.get_id(), article_product_for_review=article,
                                    scope_picture='review',
                                     path_picture=list_picture_path)
                db.session.add(add_path)
                db.session.commit()
            else:
                add_clothes = Review(user_id=current_user.get_id(), rating=rating, article_product=article,
                                     size_product=size,
                                     review=review, size_matching=size_matching, like=0, dislike=0,
                                     )
                db.session.add(add_clothes)

                db.session.commit()
            return redirect((url_for('catalog.product_details', article=article, category=category)))

    sub_query_like = db.session.query(Review_liking_check.review_id, func.sum(case([(Review_liking_check.is_like == True, 1)], else_=0)).label('sum_like'), func.sum(case([(Review_liking_check.is_dislike == True, 1)], else_=0)).label('sum_dislike'))\
                  .group_by(Review_liking_check.review_id).subquery('query_like')

    likes_current_user = db.session.query(Review.id, Review_liking_check.is_like,
     Review_liking_check.is_dislike).outerjoin(Review_liking_check,
       Review.id == Review_liking_check.review_id).filter(
        Review_liking_check.user_id == current_user.get_id()).subquery('likes_current_user')

    review_all_current_article = db.session.query(User, Review, Path_picture, Products.color, sub_query_like.c.sum_like, sub_query_like.c.sum_dislike, likes_current_user.c.is_like, likes_current_user.c.is_dislike) \
        .outerjoin(User, (Review.user_id == User.id) & (Review.article_product == article)) \
        .outerjoin(Path_picture, (Review.user_id == Path_picture.user_id) & (Review.article_product == Path_picture.article_product_for_review)).filter((Path_picture.scope_picture == 'review') | (Path_picture.scope_picture == None)) \
        .outerjoin(sub_query_like,  Review.id == sub_query_like.c.review_id)\
        .outerjoin(likes_current_user, Review.id == likes_current_user.c.id)\
        .outerjoin(Products, Review.article_product == Products.product_article).filter(
        Review.article_product == article).limit(5)
    rating_estimation_avg = db.session.query(func.avg(Review.rating)).filter_by(article_product=article).all()
    rating_count = db.session.query(Review.rating).filter_by(article_product=article).count()
    if rating_estimation_avg[0][0] == None:
        rating_estimation_avg[0] = [0]

    card_decs_price = (db.session.query(Products, Price).join(Price).filter(Products.product_article == article)).all()
    size_count = card_decs_price[0][0].product_balance.all()
    card_decs_price.append(size_count)
    return render_template('catalog/product-details-sticky-right.html', checking_review=checking_review, article=article, card=card_decs_price, form_message=form_message, review=review_all_current_article.all(), rating_count=rating_count, rating_estimation_avg=round(rating_estimation_avg[0][0]),  enumerate=enumerate)





