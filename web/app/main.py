from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from models import db, Ad
from sqlalchemy.orm import load_only
from sqlalchemy import desc, asc, func, select
import os
from flask_caching import Cache
import time

app = Flask(__name__)
db.init_app(app)
DEBUG = os.environ["FLASK_DEBUG"]
ADS_PER_PAGE = 60

POSTGRES = {
    'user': os.environ["POSTGRES_USER"],
    'pw': os.environ["POSTGRES_PASSWORD"],
    'db': os.environ["POSTGRES_DB"],
    'host': 'db',
    'port': '5432',
}

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://%(user)s:%(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
cache = Cache(app, config={'CACHE_TYPE': 'memcached', 'CACHE_MEMCACHED_SERVERS': ('memcached:11211',)})


def view_full_path_key():
    return request.full_path


@app.route("/", methods=['GET'])
@cache.cached(timeout=60*60*12, key_prefix=view_full_path_key)
def index():
    return render_template('http451.html'), 451


#@cache.cached(timeout=120, key_prefix='advertisers')
#def get_advertisers():
#    return [ad.advertiser for ad in Ad.query.options(load_only("advertiser")).order_by(Ad.advertiser).distinct("advertiser").all() if ad.advertiser is not None]
#
#
#
#def get_advertisers_and_count():
#    return [(ad.advertiser, ad.count) for ad in Ad.query.with_entities(Ad.advertiser, func.count(Ad.advertiser).label('count')).group_by(Ad.advertiser).order_by(Ad.advertiser).all() if ad.advertiser is not None]
#
#
#
#@app.route("/", methods=['GET'])
#@cache.cached(timeout=60*60*12, key_prefix=view_full_path_key)
#def index():
#
#    advertiser_filter = request.args.get('advertiser', None)
#    search_query = request.args.get('q', "")
#    page = request.args.get('page', 1, type=int)
#
#    total_adcount = Ad.query.count()
#
#    query = Ad.query
#
#    if search_query:
#       query = query.filter(func.to_tsvector('swedish', Ad.plaintext).match(search_query, postgresql_regconfig='swedish'))
#
#    if advertiser_filter:
#       query = query.filter_by(advertiser=advertiser_filter)
#       
#    adcount = query.count()
#    ads = query.order_by(desc(Ad.created_at)).paginate(page, ADS_PER_PAGE, False)
#       
#    next_url = url_for('index', page=ads.next_num, advertiser=advertiser_filter, q=search_query) if ads.has_next else None
#    prev_url = url_for('index', page=ads.prev_num, advertiser=advertiser_filter, q=search_query) if ads.has_prev else None
#
#    return render_template('index.html', \
#            ads=ads.items, \
#            advertisers=get_advertisers(), \
#            advertiser_filter=advertiser_filter, \
#            adcount=adcount, \
#            total_adcount=total_adcount, \
#            ads_per_page=ADS_PER_PAGE, \
#            next_url=next_url, \
#            prev_url=prev_url, \
#            search_query=search_query, \
#            now=time.ctime())
#
#
#
#@app.route("/ad/<string:fbid>", methods=['GET'])
#@cache.cached(timeout=60*60*12)
#def ad(fbid):
#    ad = Ad.query.filter_by(fbid=fbid).first() 
#
#    if ad:
#        return render_template('ad.html', ad=ad)
#    else:
#        abort(404)
#
#
#
#@app.route("/annonsorer", methods=['GET'])
#@cache.cached(timeout=60*60*12)
#def advertisers():
#    advertisers = get_advertisers_and_count()
#    return render_template('advertisers.html', advertisers=advertisers)


#@app.route("/om-insamlingen", methods=['GET'])
#@cache.cached(timeout=60*60*12)
#def about():
#    return render_template('about.html')
#


@app.route("/cc/<string:key>", methods=['GET'])
def cache_clear(key):
    """Drop entire cache (for debugging)
    """
    cache_key=os.environ["CACHE_CLEAR_KEY"]
    if len(cache_key) == 0:
        abort(500) # no key set

    if key == cache_key:
        cache.clear()
        return "Cache cleared %s" % time.ctime()
    else:
        abort(401)


if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host='0.0.0.0', debug=DEBUG, port=80)