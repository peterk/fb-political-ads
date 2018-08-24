from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from models import db, Ad
from sqlalchemy.orm import load_only
from sqlalchemy import desc, asc
import os
from flask_caching import Cache
import time

app = Flask(__name__)
db.init_app(app)
DEBUG = os.environ["FLASK_DEBUG"]

POSTGRES = {
    'user': os.environ["POSTGRES_USER"],
    'pw': os.environ["POSTGRES_PASSWORD"],
    'db': os.environ["POSTGRES_DB"],
    'host': 'db',
    'port': '5432',
}

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://%(user)s:%(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES
cache = Cache(app, config={'CACHE_TYPE': 'memcached', 'CACHE_MEMCACHED_SERVERS': ('memcached:11211',)})

def view_full_path_key():
    return request.full_path


@cache.cached(timeout=120, key_prefix='advertisers')
def get_advertisers():
    return [ad.advertiser for ad in Ad.query.options(load_only("advertiser")).order_by(Ad.advertiser).distinct("advertiser").all() if ad.advertiser is not None]


@app.route("/", methods=['GET'])
def index():

    advertiser_filter = request.args.get('advertiser', None)

    adcount = Ad.query.count()

    if advertiser_filter:
        ads = Ad.query.filter_by(advertiser=advertiser_filter).order_by(desc(Ad.created_at))
    else:
        ads = Ad.query.order_by(desc(Ad.created_at)).all()

    return render_template('index.html', ads=ads, advertisers=get_advertisers(), advertiser_filter=advertiser_filter, adcount=adcount)



@app.route("/ad/<string:fbid>", methods=['GET'])
@cache.cached(timeout=60*60*24)
def ad(fbid):
    ad = Ad.query.filter_by(fbid=fbid).first() 

    if ad:
        return render_template('ad.html', ad=ad)
    else:
        abort(404)



@app.route("/om-insamlingen", methods=['GET'])
@cache.cached(timeout=60*60*24)
def about():
    return render_template('about.html')



if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host='0.0.0.0', debug=DEBUG, port=80)
