from app.shopping import bp
from app import db
from flask import render_template, flash, redirect, url_for, request, render_template_string, g, \
    jsonify, current_app, session, make_response
from app.models import Category, Products, Price, Balance, Cart, Favourites, BaseModel, Review_liking_check

from app.shopping.forms import *
from flask_login import current_user, login_required
from app.models import Category, Products, Price, Balance, Review, Path_picture, User
from sqlalchemy.sql import func, case
from flask_paginate import Pagination, get_page_parameter
from werkzeug.utils import secure_filename
import json
import imghdr
import os



@bp.route('/wishlist', methods=['GET', 'POST'])
@login_required
def wishlist():
    if current_user.is_authenticated:
        clothes_wihlist = db.session.query(Favourites, Products.picture_product, Balance.count, Cart).filter_by(
            user_id=current_user.get_id()).join(
            Products, Products.product_article == Favourites.article_product).join(Balance).filter(
            (Balance.product_article_balance == Favourites.article_product) & (Balance.size == Favourites.size))\
            .outerjoin(Cart, ((Favourites.article_product == Cart.article_product) & (Cart.user_id == current_user.get_id()) & (Cart.size == Favourites.size))).all()
    return render_template('shopping/wishlist.html', clothes_wihlist=clothes_wihlist,  enumerate=enumerate)

@bp.route('/del_position_cart/<target_del>/<article>/<size>', methods=['GET', 'POST'])
def del_position_cart(article, size, target_del):
    if target_del == 'wishlist':
        if current_user.is_authenticated:
            favourites = Favourites.query.filter((Favourites.user_id == current_user.get_id())&(Favourites.article_product == article)&(Favourites.size == size)).one()
            db.session.delete(favourites)
            db.session.commit()
        return redirect(url_for('shopping.wishlist'))
    elif target_del == 'cart':
        if current_user.is_authenticated:
            cart = Cart.query.filter((Cart.user_id == current_user.get_id())&(Cart.article_product == article)&(Cart.size == size)).one()
            db.session.delete(cart)
            db.session.commit()
        elif current_user.is_anonymous:
            if request.cookies.get('cart'):
                res = request.cookies.get('cart')
                article_size_cart = json.loads(res.replace("'", '"'))
                count = '1'
                art_size = [article, size, count]
                article_size_cart.remove(art_size)
                res = make_response(redirect(url_for('shopping.cart')))
                if len(article_size_cart) == 0:
                    res.delete_cookie('cart')
                    return res
                else:
                    res.set_cookie('cart', value=str(article_size_cart), max_age=3600)
                    return res
        return redirect(url_for('shopping.cart'))



@bp.route('/sum_delivery_t', methods=[ 'POST'])
def sum_delivery_t():
    return None

def validate_image(stream):
    header = stream.read(512)
    stream.seek(0)
    format = imghdr.what(None, header)
    if not format:
        return False
    elif format == 'jpeg':
        return True
    return '.' + format in current_app.config['UPLOAD_EXTENSIONS']

@bp.route('/review_all/<article>', methods=['GET', 'POST'])
def review_all(article):
    form_sort = SortForm()
    form_message = ReviewForm()
    form_checkbox = CheckboxForm()
    checking_review = (db.session.query(func.count(Review.user_id)).filter(
        (Review.user_id == current_user.get_id()) & (Review.article_product == article)).first()[0])

    if request.method == 'GET':
        photo_stock = session.get('photo')
        sort = session.get('sort')
        sub_query_like = db.session.query(Review_liking_check.review_id,
              func.sum(case([(Review_liking_check.is_like == True, 1)], else_=0)).label(
                  'sum_like'),
              func.sum(case([(Review_liking_check.is_dislike == True, 1)], else_=0)).label(
                  'sum_dislike')) \
            .group_by(Review_liking_check.review_id).subquery('query_like')

        likes_current_user = db.session.query(Review.id, Review_liking_check.is_like,
          Review_liking_check.is_dislike).outerjoin(Review_liking_check,
            Review.id == Review_liking_check.review_id).filter(
            Review_liking_check.user_id == current_user.get_id()).subquery('likes_current_user')
        if photo_stock == 'None' or photo_stock == None:
            review_all_current_article = db.session.query(User, Review, Path_picture, Products.color,
                                                          sub_query_like.c.sum_like,
                                                          sub_query_like.c.sum_dislike, likes_current_user.c.is_like,
                                                          likes_current_user.c.is_dislike) \
                .outerjoin(User, (Review.user_id == User.id) & (Review.article_product == article)) \
                .outerjoin(Path_picture, (Review.user_id == Path_picture.user_id) & (
                    Review.article_product == Path_picture.article_product_for_review)).filter(
                (Path_picture.scope_picture == 'review') | (Path_picture.scope_picture == None)) \
                .outerjoin(sub_query_like, Review.id == sub_query_like.c.review_id) \
                .outerjoin(likes_current_user, Review.id == likes_current_user.c.id) \
                .outerjoin(Products, Review.article_product == Products.product_article).filter(
                Review.article_product == article)
        elif photo_stock == 'photo_stock':
            review_all_current_article = db.session.query(User, Review, Path_picture, Products.color,
                                                          sub_query_like.c.sum_like,
                                                          sub_query_like.c.sum_dislike, likes_current_user.c.is_like,
                                                          likes_current_user.c.is_dislike) \
                .outerjoin(User, (Review.user_id == User.id) & (Review.article_product == article)) \
                .join(Path_picture, (Review.user_id == Path_picture.user_id) & (
                    Review.article_product == Path_picture.article_product_for_review)).filter(
                (Path_picture.scope_picture == 'review') | (Path_picture.scope_picture == None)) \
                .outerjoin(sub_query_like, Review.id == sub_query_like.c.review_id) \
                .outerjoin(likes_current_user, Review.id == likes_current_user.c.id) \
                .outerjoin(Products, Review.article_product == Products.product_article).filter(
                Review.article_product == article)
        if sort == 'Date.max':
            review_all_current_article = review_all_current_article.order_by(Review.time_create)
        elif sort == 'Date.min':
            review_all_current_article = review_all_current_article.order_by(Review.time_create.desc())
        elif sort == 'Rating.max':
            review_all_current_article = review_all_current_article.order_by(Review.rating.desc())
        elif sort == 'Rating.min':
            review_all_current_article = review_all_current_article.order_by(Review.rating)
        elif sort == 'Useful.max':
            review_all_current_article = review_all_current_article.order_by(
                sub_query_like.c.sum_dislike.desc())
        elif sort == 'Useful.min':
            review_all_current_article = review_all_current_article.order_by(sub_query_like.c.sum_like.desc())
        else:
            review_all_current_article = review_all_current_article

    if request.method == 'POST':
        if 'sort' not in request.form:
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


        photo = request.form.get('photo_stock')
        if form_sort.sort.data != None and photo != None:
            session['sort'] = form_sort.sort.data
            session['photo'] = str(photo)
        else:
            session['sort'] = form_sort.sort.data
            session['photo'] = None
        return redirect(url_for('shopping.review_all', article=article))
    elif request.method == 'GET':
        if session.get('sort') != None:
            sort_data = session.get('sort')
            photo_data = session.get('photo')
            form_sort.sort.data = sort_data
            form_checkbox.photo_stock.data = photo_data


    card_decs_price = (db.session.query(Products, Price).join(Price).filter(Products.product_article == article)).all()
    size_count = card_decs_price[0][
        0].product_balance.all()

    card_decs_price.append(size_count)
    rating_estimation_avg = db.session.query(func.avg(Review.rating)).filter_by(article_product=article).all()
    rating_count = db.session.query(Review.rating).filter_by(article_product=article).count()
    if rating_estimation_avg[0][0] == None:
        rating_estimation_avg[0] = [0]

    page = request.args.get('page', 1, type=int)

    pagination = Pagination(page=page, per_page=current_app.config['POSTS_PER_PAGE_REVIEW'],
                            display_msg="Displayed <span> {start} - {end} </span> of <span> {total} </span> of results",
                            total=review_all_current_article.count(), search=False, record_name='clothess')
    review_all_current_article = review_all_current_article.paginate(page, current_app.config['POSTS_PER_PAGE_REVIEW'], False)



    return render_template('shopping/review_all_one_article.html', checking_review=checking_review, form_sort=form_sort, form_checkbox=form_checkbox, pagination=pagination, review=review_all_current_article.items, form_message=form_message, article=article, card=card_decs_price, rating_count=rating_count, rating_estimation_avg=round(rating_estimation_avg[0][0]), enumerate=enumerate)




@bp.route('/like_dislike', methods=[ 'POST'])
def like_and_dislike():
    put = request.form['put']
    id_target = request.form['target_review']
    is_like = True
    if current_user.is_authenticated:
        if put == 'like':
            review_cheking_like = db.session.query(Review_liking_check) \
                .filter(
                (Review_liking_check.review_id == id_target) & (Review_liking_check.user_id == current_user.get_id())
                & (Review_liking_check.is_dislike == True)).first()
            if review_cheking_like != None:
                review_like_move_dis = db.session.query(Review_liking_check).get(review_cheking_like.id)
                review_like_move_dis.is_like = True
                review_like_move_dis.is_dislike = False
                db.session.add(review_like_move_dis)
                db.session.commit()

                review_count_dislike = db.session.query(
                    func.sum(case([(Review_liking_check.is_dislike == True, 1)], else_=0)).label('sum_dis'),
                    func.sum(case([(Review_liking_check.is_like == True, 1)], else_=0)).label('sum_like')) \
                    .filter(Review_liking_check.review_id == id_target).first()

                count = (str(review_count_dislike.sum_dis) + ' ' + str(review_count_dislike.sum_like)  + ' ' + '1')

                if review_count_dislike[0] == None and review_count_dislike[1] == None:
                    count = '0 0'
                return count


            review_check = db.session.query(Review_liking_check)\
                .filter((Review_liking_check.review_id == id_target) & (Review_liking_check.user_id == current_user.get_id())
                                                                        & (Review_liking_check.is_like == True)).first()


            if  review_check != None:
                review_like_del = db.session.query(Review_liking_check).filter((Review_liking_check.review_id == id_target) & (Review_liking_check.user_id == current_user.get_id())).one()
                db.session.delete(review_like_del)
                db.session.commit()

                review_count_dislike = db.session.query(
                    func.sum(case([(Review_liking_check.is_dislike == True, 1)], else_=0)).label('sum_dis'),
                    func.sum(case([(Review_liking_check.is_like == True, 1)], else_=0)).label('sum_like')) \
                    .filter(Review_liking_check.review_id == id_target).first()

                count = (str(review_count_dislike.sum_dis) + ' ' + str(review_count_dislike.sum_like)  + ' ' + '0')

                if review_count_dislike[0] == None and review_count_dislike[1] == None:
                    count = '0 0'
                return count

            elif  review_check == None:
                add_liking_check = Review_liking_check(review_id=id_target, user_id=current_user.get_id(),
                                                       is_like=is_like,
                                                       is_dislike=not is_like)
                db.session.add(add_liking_check)
                db.session.commit()
                review_count_dislike = db.session.query(
                    func.sum(case([(Review_liking_check.is_dislike == True, 1)], else_=0)).label('sum_dis'),
                    func.sum(case([(Review_liking_check.is_like == True, 1)], else_=0)).label('sum_like')) \
                    .filter(Review_liking_check.review_id == id_target).first()

                count = (str(review_count_dislike.sum_dis) + ' ' + str(review_count_dislike.sum_like)  + ' ' + '1')
                if review_count_dislike[0] == None and review_count_dislike[1] == None:
                    count = '0 0'
                return count
        elif put == 'dislike':
            review_cheking_like = db.session.query(Review_liking_check) \
                .filter(
                (Review_liking_check.review_id == id_target) & (Review_liking_check.user_id == current_user.get_id())
                & (Review_liking_check.is_like == True)).first()
            if review_cheking_like != None:
                review_like_move_dis = db.session.query(Review_liking_check).get(review_cheking_like.id)
                review_like_move_dis.is_like = False
                review_like_move_dis.is_dislike = True
                db.session.add(review_like_move_dis)
                db.session.commit()

                review_count_dislike = db.session.query(
                    func.sum(case([(Review_liking_check.is_dislike == True, 1)], else_=0)).label('sum_dis'),
                    func.sum(case([(Review_liking_check.is_like == True, 1)], else_=0)).label('sum_like')) \
                    .filter(Review_liking_check.review_id == id_target).first()

                count = (str(review_count_dislike.sum_dis) + ' ' + str(review_count_dislike.sum_like)  + ' ' + '1')
                if review_count_dislike[0] == None and review_count_dislike[1] == None:
                    count = '0 0'
                return count

            review_check = db.session.query(Review_liking_check) \
                .filter(
                (Review_liking_check.review_id == id_target) & (Review_liking_check.user_id == current_user.get_id())
                & (Review_liking_check.is_dislike == True)).first()

            if review_check != None:
                review_like_del = db.session.query(Review_liking_check).filter(
                    (Review_liking_check.review_id == id_target) & (
                                Review_liking_check.user_id == current_user.get_id())).one()
                db.session.delete(review_like_del)
                db.session.commit()

                review_count_dislike = db.session.query(
                    func.sum(case([(Review_liking_check.is_dislike == True, 1)], else_=0)).label('sum_dis'),
                    func.sum(case([(Review_liking_check.is_like == True, 1)], else_=0)).label('sum_like')) \
                    .filter(Review_liking_check.review_id == id_target).first()

                count = (str(review_count_dislike.sum_dis) + ' ' + str(review_count_dislike.sum_like) + ' ' + '0')
                if review_count_dislike[0] == None and review_count_dislike[1] == None:
                    count = '0 0'
                return count

            elif review_check == None:
                is_like = False
                add_liking_check = Review_liking_check(review_id=id_target, user_id=current_user.get_id(),
                                                       is_like=is_like,
                                                       is_dislike=not is_like)
                db.session.add(add_liking_check)
                db.session.commit()
                review_count_dislike = db.session.query(
                    func.sum(case([(Review_liking_check.is_dislike == True, 1)], else_=0)).label('sum_dis'), func.sum(case([(Review_liking_check.is_like == True, 1)], else_=0)).label('sum_like')) \
                    .filter(Review_liking_check.review_id == id_target).first()
                count = (str(review_count_dislike.sum_dis) + ' ' + str(review_count_dislike.sum_like)  + ' ' + '1')
                if review_count_dislike[0] == None and review_count_dislike[1] == None:
                    count = '0 0'
                return count
    else:
        return str(None)
    return str(0)

@bp.route('/sort_review', methods=['GET', 'POST'])
def sort_review():
    sort_dir = request.form['direction']
    sort_type = request.form['sort_type']
    article = request.form['current_article']
    sub_query_like = db.session.query(Review_liking_check.review_id,
                                      func.sum(case([(Review_liking_check.is_like == True, 1)], else_=0)).label(
                                          'sum_like'),
                                      func.sum(case([(Review_liking_check.is_dislike == True, 1)], else_=0)).label(
                                          'sum_dislike')) \
        .group_by(Review_liking_check.review_id).subquery('query_like')

    likes_current_user = db.session.query(Review.id, Review_liking_check.is_like,
                                          Review_liking_check.is_dislike).outerjoin(Review_liking_check,
                                                                                    Review.id == Review_liking_check.review_id).filter(
        Review_liking_check.user_id == current_user.get_id()).subquery('likes_current_user')

    review_all_current_article = db.session.query(User, Review, Path_picture, Products.color, sub_query_like.c.sum_like,
                                                  sub_query_like.c.sum_dislike, likes_current_user.c.is_like,
                                                  likes_current_user.c.is_dislike) \
        .outerjoin(User, (Review.user_id == User.id) & (Review.article_product == article)) \
        .outerjoin(Path_picture, (Review.user_id == Path_picture.user_id) & (
                Review.article_product == Path_picture.article_product_for_review)).filter(
        (Path_picture.scope_picture == 'review') | (Path_picture.scope_picture == None)) \
        .outerjoin(sub_query_like, Review.id == sub_query_like.c.review_id) \
        .outerjoin(likes_current_user, Review.id == likes_current_user.c.id) \
        .outerjoin(Products, Review.article_product == Products.product_article).filter(
        Review.article_product == article)
    if sort_type == 'date':
        if sort_dir == 'true':
            review_all_current_article = review_all_current_article.order_by(Review.time_create).limit(5)
        elif sort_dir == 'false':
            review_all_current_article = review_all_current_article.order_by(Review.time_create.desc()).limit(5)
    elif sort_type == 'rating':

        if sort_dir == 'true':
            review_all_current_article = review_all_current_article.order_by(Review.rating).limit(5)
        elif sort_dir == 'false':
            review_all_current_article = review_all_current_article.order_by(Review.rating.desc()).limit(5)
    elif sort_type == 'useful':
        if sort_dir == 'true':
            review_all_current_article = review_all_current_article.order_by(sub_query_like.c.sum_dislike.desc()).limit(5)
        elif sort_dir == 'false':
            review_all_current_article = review_all_current_article.order_by(sub_query_like.c.sum_like.desc()).limit(5)
    elif sort_type == 'photo_stock':
        if sort_dir == 'true':
            sub_query_like = db.session.query(Review_liking_check.review_id,
                                              func.sum(case([(Review_liking_check.is_like == True, 1)], else_=0)).label(
                                                  'sum_like'), func.sum(
                    case([(Review_liking_check.is_dislike == True, 1)], else_=0)).label('sum_dislike')) \
                .group_by(Review_liking_check.review_id).subquery('query_like')

            likes_current_user = db.session.query(Review.id, Review_liking_check.is_like,
                                                  Review_liking_check.is_dislike).outerjoin(Review_liking_check,
                                                                                            Review.id == Review_liking_check.review_id).filter(
                Review_liking_check.user_id == current_user.get_id()).subquery('likes_current_user')

            review_all_current_article = db.session.query(User, Review, Path_picture, Products.color,
                                                          sub_query_like.c.sum_like, sub_query_like.c.sum_dislike,
                                                          likes_current_user.c.is_like, likes_current_user.c.is_dislike) \
                .outerjoin(User, (Review.user_id == User.id) & (Review.article_product == article)) \
                .join(Path_picture, (Review.user_id == Path_picture.user_id) & (
                        Review.article_product == Path_picture.article_product_for_review)).filter(
                (Path_picture.scope_picture == 'review') | (Path_picture.scope_picture == None)) \
                .outerjoin(sub_query_like, Review.id == sub_query_like.c.review_id) \
                .outerjoin(likes_current_user, Review.id == likes_current_user.c.id) \
                .outerjoin(Products, Review.article_product == Products.product_article).filter(
                Review.article_product == article).limit(5)
        elif sort_dir == 'false':
            '''без сортировки'''

    like_current_user = db.session.query(Review.id, Review_liking_check.is_like,
     Review_liking_check.is_dislike).outerjoin(Review_liking_check,
       Review.id == Review_liking_check.review_id).filter(
        Review_liking_check.user_id == current_user.get_id()).all()
    return render_template('shopping/sort_review_ajax.html', review=review_all_current_article, like_diss_current_user = like_current_user, enumerate = enumerate)


@bp.route('/sum_delivery', methods=['POST'])
def sum_delivery():
    price = request.form['price']
    sum_cart = 0
    if current_user.is_authenticated:
        clothes_cart = db.session.query(Cart, Products.picture_product).filter_by(user_id=current_user.get_id()).join(
            Products).filter(Products.product_article == Cart.article_product).all()

        for i in clothes_cart:
            sum_cart += i[0].current_price
    elif current_user.is_anonymous:
        if request.cookies.get('cart'):
            res = request.cookies.get('cart')
            article_size_cart = json.loads(res.replace("'", '"'))
            clothes_cart = []
            for i in article_size_cart:
                request_clothes = (
                    db.session.query(Products, Price, Balance).join(Price).filter(
                        Products.product_article == i[0])
                        .join(Balance).filter(
                        (Balance.size == i[1]) & (Balance.product_article_balance == i[0]))).all()
                clothes_cart += request_clothes
            for i in clothes_cart:
                sum_cart += i[1].current_price
        else:
            clothes_cart = None
    sum_total = sum_cart + int(price)
    return str(sum_total)

@bp.route('/cart', methods=['GET', 'POST'])
def cart():
    sum_cart = 0
    if current_user.is_authenticated:
        clothes_cart = db.session.query(Cart, Products.picture_product, Balance).filter_by(user_id=current_user.get_id()).join(
            Products, Products.product_article == Cart.article_product).join(Balance).filter(
                        (Balance.size == Cart.size) & (Balance.product_article_balance == Cart.article_product)).all()

        for i in clothes_cart:
            sum_cart += i[0].current_price
    elif current_user.is_anonymous:
        if request.cookies.get('cart'):
            res = request.cookies.get('cart')
            article_size_cart = json.loads(res.replace("'", '"'))
            clothes_cart = []
            for i in article_size_cart:
                request_clothes = (
                    db.session.query(Products, Price, Balance).join(Price).filter(
                        Products.product_article == i[0])
                        .join(Balance).filter(
                        (Balance.size == i[1]) & (Balance.product_article_balance == i[0]))).all()
                clothes_cart += request_clothes
            for i in clothes_cart:
                sum_cart += i[1].current_price
        else:
            clothes_cart = None
    return render_template('shopping/cart.html', cart_data=clothes_cart, sum_cart=sum_cart)


class SetEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj)
        return json.JSONEncoder.default(self, obj)

@bp.route('/put_cart', methods=['GET', 'POST'])
def put_cart():
    article = request.form['article']
    size = request.form['size']
    clothes = (
        db.session.query(Products, Price, Balance).join(Price).filter(
            Products.product_article == article)
            .join(Balance).filter(
            (Balance.size == size) & (
                Balance.product_article_balance == article)))
    request_clothes = clothes.all()
    if current_user.is_authenticated:
        clothes_cheking = db.session.query(Cart).filter((Cart.article_product == article) & (Cart.size == size) & (Cart.user_id == current_user.get_id())).count()
        if clothes_cheking == 0:
            add_clothes = Cart(user_id=current_user.get_id(), article_product=article, count='1', size=size, color=request_clothes[0][0].color,
                               current_price=request_clothes[0][1].current_price, old_price=request_clothes[0][1].old_price, name=request_clothes[0][0].name)
            db.session.add(add_clothes)
            db.session.commit()
            clothes_cart = db.session.query(Cart).filter_by(user_id=current_user.get_id()).count()
            return str(clothes_cart)
        else:
            clothes_cart = db.session.query(Cart).filter_by(user_id=current_user.get_id()).count()
            return str(clothes_cart)
    elif current_user.is_anonymous:
        count = '1'
        list_cart = [[article, size, count]]
        if request.cookies.get('cart'):
            res = request.cookies.get('cart')
            article_size_cart = json.loads(res.replace("'", '"'))
            count = 0
            count2 = 0
            for i in article_size_cart:
                for a in i:
                    if a == list_cart[0][0]:
                        count += 1
                        break
                    elif a == list_cart[0][1]:
                        count2 += 1
                        break
            if count == count2 and count >= 1:
                resp = make_response(str(len(article_size_cart[0])))
                resp.set_cookie('cart', value=str(article_size_cart), max_age=3600)
                return resp
            else:
                article_size_cart.extend(list_cart)
                article_size = article_size_cart
                resp = make_response(str(len(article_size[0])))
                resp.set_cookie('cart', value=str(article_size), max_age=3600)
                return resp
        else:
            resp = make_response(str(len(list_cart)))
            resp.set_cookie('cart', value=str(list_cart), max_age=3600)
            return resp

@bp.route('/put_wishlist', methods=['GET', 'POST'])
@login_required
def put_wishlist():
    article = request.form['article']
    size = request.form['size']
    clothes = (
        db.session.query(Products, Price, Balance).join(Price).filter(
            Products.product_article == article)
            .join(Balance).filter(
            (Balance.size == size) & (
                    Balance.product_article_balance == article)))
    request_clothes = clothes.all()
    if current_user.is_authenticated:
        clothes_cheking = db.session.query(Favourites).filter((Favourites.article_product == article) & (Favourites.size == size) & Favourites.user_id == current_user.get_id()).count()
        if clothes_cheking == 0:
            add_clothes = Favourites(user_id=current_user.get_id(), article_product=article, count='1', size=size,
                               color=request_clothes[0][0].color,
                               current_price=request_clothes[0][1].current_price,
                               old_price=request_clothes[0][1].old_price, name=request_clothes[0][0].name)
            db.session.add(add_clothes)
            db.session.commit()
            clothes_cart = db.session.query(Favourites).filter_by(user_id=current_user.get_id()).count()
            return str(clothes_cart)
        else:
            clothes_cart = db.session.query(Favourites).filter_by(user_id=current_user.get_id()).count()
            return str(clothes_cart)
    return ""

@bp.route('/cart_visible', methods=['POST'])
def cart_visible():
    res = request.cookies.get('cart')
    list = []
    if current_user.is_authenticated:
        clothes_cart = db.session.query(Cart).filter_by(user_id=current_user.get_id()).count()
        return str(clothes_cart)
    elif current_user.is_anonymous:
        if res != None:
            article_size_cart = json.loads(res.replace("'", '"'))
            for i in article_size_cart:
                request_clothes = (
                    db.session.query(Products, Price, Balance).join(Price).filter(
                        Products.product_article == (i[0]))
                        .join(Balance).filter(
                        (Balance.size == (i[1])) & (
                            Balance.product_article_balance == (i[0])))).all()
                list += (request_clothes)
        else:
            request_clothes = 0
            return str(request_clothes)


    return str(len(article_size_cart))