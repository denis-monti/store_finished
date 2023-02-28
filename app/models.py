from datetime import datetime, timedelta

from app import db
from app import login
from sqlalchemy.orm.attributes import QueryableAttribute
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from flask import current_app, url_for, json

from app.search import add_to_index, remove_from_index, query_index

class SearchableMixin(object):
    # @classmethod
    # def search(cls, expression, page, per_page, sort_data):
    #     ids, total, ids_sum = query_index(cls.__tablename__, expression, page, per_page)
    #     if total['value'] == 0:
    #         return cls.query.filter_by(id_Product=0), 0, []
    #     when = []
    #     for i in range(len(ids)):
    #         when.append((ids[i], i))
    #     print()
    #     return db.session.query(cls, Price).filter(cls.id_Product.in_(ids)).join(Price,
    #         Products.product_article == Price.product_article_price).order_by(
    #         db.case(when, value=cls.id_Product)), total['value'], ids_sum
    @classmethod
    def search(cls, expression, page):
        total, ids_sum = query_index(cls.__tablename__, expression, page)
        return total['value'], ids_sum
        cls.reindex()


    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }
        cls.reindex()

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None
        cls.reindex()

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)



db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)



class BaseModel(db.Model):
    __abstract__ = True

    def to_dict(self, show=None, _hide=None, _path=None):
        """Return a dictionary representation of this model."""

        show = show or []
        _hide = _hide or []

        hidden = self._hidden_fields if hasattr(self, "_hidden_fields") else []
        default = self._default_fields if hasattr(self, "_default_fields") else []
        default.extend(['id', 'modified_at', 'created_at'])

        if not _path:
            _path = self.__tablename__.lower()

            def prepend_path(item):
                item = item.lower()
                if item.split(".", 1)[0] == _path:
                    return item
                if len(item) == 0:
                    return item
                if item[0] != ".":
                    item = ".%s" % item
                item = "%s%s" % (_path, item)
                return item

            _hide[:] = [prepend_path(x) for x in _hide]
            show[:] = [prepend_path(x) for x in show]

        columns = self.__table__.columns.keys()
        relationships = self.__mapper__.relationships.keys()
        properties = dir(self)

        ret_data = {}

        for key in columns:
            if key.startswith("_"):
                continue
            check = "%s.%s" % (_path, key)
            if check in _hide or key in hidden:
                continue
            if check in show or key in default:
                ret_data[key] = getattr(self, key)

        for key in relationships:
            if key.startswith("_"):
                continue
            check = "%s.%s" % (_path, key)
            if check in _hide or key in hidden:
                continue
            if check in show or key in default:
                _hide.append(check)
                is_list = self.__mapper__.relationships[key].uselist
                if is_list:
                    items = getattr(self, key)
                    if self.__mapper__.relationships[key].query_class is not None:
                        if hasattr(items, "all"):
                            items = items.all()
                    ret_data[key] = []
                    for item in items:
                        ret_data[key].append(
                            item.to_dict(
                                show=list(show),
                                _hide=list(_hide),
                                _path=("%s.%s" % (_path, key.lower())),
                            )
                        )
                else:
                    if (
                        self.__mapper__.relationships[key].query_class is not None
                        or self.__mapper__.relationships[key].instrument_class
                        is not None
                    ):
                        item = getattr(self, key)
                        if item is not None:
                            ret_data[key] = item.to_dict(
                                show=list(show),
                                _hide=list(_hide),
                                _path=("%s.%s" % (_path, key.lower())),
                            )
                        else:
                            ret_data[key] = None
                    else:
                        ret_data[key] = getattr(self, key)

        for key in list(set(properties) - set(columns) - set(relationships)):
            if key.startswith("_"):
                continue
            if not hasattr(self.__class__, key):
                continue
            attr = getattr(self.__class__, key)
            if not (isinstance(attr, property) or isinstance(attr, QueryableAttribute)):
                continue
            check = "%s.%s" % (_path, key)
            if check in _hide or key in hidden:
                continue
            if check in show or key in default:
                val = getattr(self, key)
                if hasattr(val, "to_dict"):
                    ret_data[key] = val.to_dict(
                        show=list(show),
                        _hide=list(_hide),
                        _path=('%s.%s' % (_path, key.lower())),
                    )
                else:
                    try:
                        ret_data[key] = json.loads(json.dumps(val))
                    except:
                        pass

        return ret_data

class Category(db.Model):
    id_category = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer)
    level = db.Column(db.Integer)
    name = db.Column(db.String(128), index=True)
    category = db.relationship('Products', backref='category', lazy='dynamic')

    def __repr__(self):
        return '<Сategory {} {} {} {}>'.format(self.id_category, self.parent_id, self.level, self.name)

class Products(SearchableMixin, BaseModel, db.Model):
    __searchable__ = ['name', 'brand']
    id_Product = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(128))
    category_product = db.Column(db.String(128), db.ForeignKey('category.name'))
    product_balance = db.relationship('Balance', backref='products', lazy='dynamic')
    product_price = db.relationship('Price', backref='products', lazy='dynamic')
    product_favourites = db.relationship('Favourites', backref='products', lazy='dynamic')
    product_cart = db.relationship('Cart', backref='products', lazy='dynamic')
    name = db.Column(db.String(128))
    product_article = db.Column(db.String(128), unique=True)
    description = db.Column(db.String(512))
    color = db.Column(db.String(64))
    season = db.Column(db.String(64))
    picture_product = db.Column(db.String(128))
    composition = db.Column(db.String(128))
    specifications = db.Column(db.String(1024))
    complete_set = db.Column(db.String(128))

    _default_fields = [
        "brand",
        "category_product",
        "name",
        "product_article",
        "color",
    ]


    def __repr__(self):
        return '<Products {} {} {} {} {}>'.format(self.id_Product, self.brand, self.product_article, self.category_product, self.picture_product)


class Balance(BaseModel, db.Model):
    id_balance = db.Column(db.Integer, primary_key=True)
    product_article_balance = db.Column(db.String(128), db.ForeignKey('products.product_article'))
    size = db.Column(db.Integer)
    count = db.Column(db.Integer)

    _default_fields = [
        "size",
        "count",
    ]


class Price(BaseModel, db.Model):
    id_balance = db.Column(db.Integer, primary_key=True)
    product_article_price = db.Column(db.String(128), db.ForeignKey('products.product_article'), unique=True)
    current_price = db.Column(db.Integer)
    old_price = db.Column(db.Integer)

    _default_fields = [
        "current_price",
        "old_price",
    ]

    def __repr__(self):
        return '<Price {} {} {} {}>'.format(self.id_balance, self.product_article_price, self.current_price, self.old_price)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    favourites_product = db.relationship('Favourites', backref='user', lazy='dynamic')
    basket_product = db.relationship('Cart', backref='user', lazy='dynamic')
    review_product = db.relationship('Review', backref='user', lazy='dynamic')
    picture_current_profile = db.relationship('Path_picture', backref='user', lazy='dynamic')

    def __repr__(self):
        return '<User {} {} {} {}>'.format(self.id, self.username, self.email, self.last_seen)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)




@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Favourites(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    article_product = db.Column(db.String(128), db.ForeignKey('products.product_article'))
    name = db.Column(db.String(128))
    count = db.Column(db.Integer)
    size = db.Column(db.Integer)
    color = db.Column(db.String(128))
    current_price = db.Column(db.Integer)
    old_price = db.Column(db.Integer)
    time_create = db.Column(db.DateTime, default=datetime.utcnow)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    article_product = db.Column(db.String(128), db.ForeignKey('products.product_article'))
    name = db.Column(db.String(128))
    count = db.Column(db.Integer)
    size = db.Column(db.Integer)
    color = db.Column(db.String(128))
    current_price = db.Column(db.Integer)
    old_price = db.Column(db.Integer)
    time_create = db.Column(db.DateTime, default=datetime.utcnow)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    rating = db.Column(db.Integer)
    article_product = db.Column(db.String(128), db.ForeignKey('products.product_article'))
    size_product = db.Column(db.String(128))
    review = db.Column(db.String(1024))
    size_matching = db.Column(db.String(128))

    time_create = db.Column(db.DateTime, default=datetime.utcnow)
    like = db.Column(db.Integer)
    dislike = db.Column(db.Integer)


class Path_picture(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    article_product_for_review = db.Column(db.String(128), db.ForeignKey('review.article_product'))
    scope_picture = db.Column(db.String(128))
    path_picture = db.Column(db.String(1024))


class Review_liking_check(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_like = db.Column(db.Boolean)
    is_dislike = db.Column(db.Boolean)