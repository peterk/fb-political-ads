import argparse
import requests
import json
import os
from urllib.parse import urlparse
import sys
import math
from models import Ad
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from lxml import html
from lxml.etree import tostring
from urllib.parse import urlparse
import shutil


archive_dir = "/app/static/ad"


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

def delete_ad(fbid, dry_run = True):
    print("Deleting %s" % fbid)
    ad_folder = os.path.join(archive_dir, str(fbid))
    
    #delete from db
    adcount = session.query(Ad).filter_by(fbid=str(fbid)).count()
    print("Found %s in db for %s" % (adcount, fbid))

    if not dry_run:
        session.query(Ad).filter_by(fbid=str(fbid)).delete()
        session.commit()
        print("Deleted %s from db" % fbid)

        #delete folder
        if os.path.exists(ad_folder):
            shutil.rmtree(ad_folder)
            print("Deleted folder %s" % ad_folder)
        else:
            print("Skipping folder - not found")
    else:
        print("Dry run so not deleting folder %s" % ad_folder)



if __name__=="__main__":
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--dryrun", help="Try it without doing it", action="store_true")
    parser.add_argument('integers', metavar='N', type=int, nargs='+', help='FB Ad ids')

    args = parser.parse_args()
    ads = args.integers
    print("Working on %s" % str(ads))

    for adid in ads:
        delete_ad(adid, args.dryrun)
