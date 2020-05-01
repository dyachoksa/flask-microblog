import datetime as dt
from hashlib import md5
from time import time

import jwt
from flask import current_app
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login_manager

followers = db.Table(
    "followers",
    db.Column("follower_id", db.Integer, db.ForeignKey("user.id"), index=True),
    db.Column("followed_id", db.Integer, db.ForeignKey("user.id"), index=True),
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=dt.datetime.utcnow)

    posts = db.relationship("Post", backref="author", lazy="dynamic")
    followed = db.relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref("followers", lazy="dynamic"),
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        data = {"reset_password": self.id, "exp": time() + expires_in}

        token = jwt.encode(data, current_app.config["SECRET_KEY"], algorithm="HS256")
        return token.decode("utf-8")

    @staticmethod
    def verify_reset_password_token(token):
        try:
            token = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )
            id = token["reset_password"]
        except jwt.DecodeError:
            return

        return User.query.get(id)

    def avatar(self, size):
        digest = md5(self.email.lower().encode("utf-8")).hexdigest()
        return "https://www.gravatar.com/avatar/{}?d=identicon&s={}".format(
            digest, size
        )

    def follow(self, user: "User"):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user: "User"):
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user: "User"):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)
        ).filter(followers.c.follower_id == self.id)

        own = Post.query.filter_by(user_id=self.id)

        return followed.union(own).order_by(Post.timestamp.desc())


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=dt.datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    language = db.Column(db.String(5))

    def __repr__(self):
        return f"<Post id={self.id} body={self.body} language={self.language}>"


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))
