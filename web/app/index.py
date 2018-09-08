import argparse
import requests
import json
import os
from urllib.parse import urlparse
import sys
import math
from models import Ad
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from lxml import html
from lxml.etree import tostring
from urllib.parse import urlparse
import shutil
from fetch_ads_by_likelihood import html2text


POSTGRES = {
    'user': os.environ["POSTGRES_USER"],
    'pw': os.environ["POSTGRES_PASSWORD"],
    'db': os.environ["POSTGRES_DB"],
    'host': 'db',
    'port': '5432',
}

dburi = 'postgresql://%(user)s:%(pw)s@%(host)s:%(port)s/%(db)s' % POSTGRES

dbngine = create_engine(dburi)
Session = sessionmaker(bind=dbngine)
session = Session()

if __name__=="__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--dryrun", help="Try it without doing it", action="store_true")

    args = parser.parse_args()
    ads = session.query(Ad).order_by(desc(Ad.created_at)).all()

    print("Rebuilding plaintext for all ads")

    for ad in ads:
        print("Working on %s" % ad.fbid)
        if not ad.plaintext:
            ad.plaintext = html2text(ad.raw["html"])
            print("\tUpdating plaintext")

        if not ad.plaintarget and "targeting" in ad.raw.keys():
            if ad.raw["targeting"]:
                ad.plaintarget = html2text(ad.raw["targeting"])
                print("\tUpdating plaintarget")
            else:
                print("\tNo targeting")

        if not args.dryrun:
            session.commit()
        else:
            print("\tDry run. not saving")


