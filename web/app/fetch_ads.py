import requests
import json
import os
from urllib.parse import urlparse
import sys
import math
from models import Ad
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

archive_dir = "/app/static/ad"
print("Working on", archive_dir)

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


def save_file(url, targetdir):
    r = requests.get(url)
    if r.status_code == requests.codes.ok:
        a = urlparse(url)
        fname = os.path.basename(a.path)
        with open(os.path.join(targetdir, fname), 'wb') as f:
            f.write(r.content)



def write_ad(jad):
    target = os.path.join(archive_dir, jad["id"])
    if not os.path.exists(target) and not "Byggmax" in jad["title"] and not "Bauhaus" in jad["title"] and not "Adlibris" in jad["title"]:
        os.makedirs(target)
        filename = jad["id"]  + ".json"
        with open(os.path.join(target, filename), 'w') as outfile:
            json.dump(jad, outfile)

        # write media
        for item in jad["images"]:
            save_file(item, target)

        if "thumbnail" in jad.keys():
            save_file(jad["thumbnail"], target)

        # clean targeting
        if jad["targetings"]:
            clean_targets = []
            print("Raw targets: %s" % len(jad["targetings"]))
            for target in jad["targetings"]:
                if target not in clean_targets:
                    clean_targets.append(target)
                else:
                    print("Skipping existing target")

            jad["targetings"] = clean_targets


        ad = Ad()
        ad.fbid=jad["id"]
        ad.advertiser=jad["advertiser"]
        ad.message=jad["message"]
        ad.raw=jad
        ad.created_at = jad["created_at"]
        ad.updated_at=jad["updated_at"]

        session.add(ad)
        session.commit()

    else:
        #This ad is already saved
        print("Already saved %s" % jad["id"])


#try:
headers = {'Accept-Language': 'sv-SE'}
r = requests.get('https://projects.propublica.org/facebook-ads/ads', headers=headers)
if r.status_code == requests.codes.ok:
    jdata = r.json()
    print("Found %s ads" % len(jdata["ads"]))
    print("Total adcount: %s" % jdata["total"])
    pages = math.ceil((jdata["total"]) / 20)
    print("Pages: %s" % pages)

    # delete old records
    deleted_count = session.query(Ad).delete()
    session.commit()
    print("Deleted %s ads from db" % deleted_count)

    for page in range(1, pages):
        r = requests.get(f"https://projects.propublica.org/facebook-ads/ads?page={page}", headers=headers)
        if r.status_code == requests.codes.ok:
            jdata = r.json()
            for ad in jdata["ads"]:
                adid = ad["id"]
                print(ad["id"])
                write_ad(ad)

#except Exception as e:
#    print(e)
