from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from models import db, Ad
from sqlalchemy.orm import load_only
import os

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


@app.route("/", methods=['GET'])
def index():

    advertiser_filter = request.args.get('advertiser', None)

    advertisers = [ad.advertiser for ad in Ad.query.options(load_only("advertiser")).order_by(Ad.advertiser).distinct("advertiser").all() if ad.advertiser is not None]

    ads = Ad.query.all()
    if advertiser_filter:
        ads = Ad.query.filter_by(advertiser=advertiser_filter)

    return render_template('index.html', ads=ads, advertisers=advertisers, advertiser_filter=advertiser_filter)


@app.route("/ad/<string:fbid>", methods=['GET'])
def ad(fbid):
    ad = Ad.query.filter_by(fbid=fbid).first() 

    if ad:
        return render_template('ad.html', ad=ad)
    else:
        abort(404)

if __name__ == "__main__":
    # Only for debugging while developing
    app.run(host='0.0.0.0', debug=DEBUG, port=80)
