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



def normalize_data(jdata):
    """Some of the older ads are missing fields. Repairing."""

    tree = html.fromstring(jdata["html"])

    # images
    if not "images" in jdata.keys():
        # parse html and extract image urls
        images = tree.xpath('//img[@src]')
        jdata["images"] = [el.get("src") for el in images]

    # advertiser
    if "advertiser" in jdata.keys():
        if jdata["advertiser"] == "" or jdata["advertiser"] is None:
            jdata["advertiser"] = jdata["title"]
    else:
        jdata["advertiser"] = jdata["title"]


    # message
    if not "message" in jdata.keys():
        msgitems = tree.xpath("//div[@class='text_exposed_root']/*")
        message = ""
        for item in msgitems:
            message += tostring(item, encoding = "unicode")

        jdata["message"] = message

    # default updated_at
    if not "updated_at" in jdata.keys():
        jdata["updated_at"] = jdata["created_at"]


    # empty targetings
    if not "targetings" in jdata.keys():
        jdata["targetings"] = []

    return jdata



def is_url(x):
    try:
        result = urlparse(x)
        if result.scheme and result.netloc and result.path:
            return True
    except:
        return False



def save_file(url, targetdir):
    print(f"Saving url: > {url} <")
    if is_url(url):
        r = requests.get(url)
        if r.status_code == requests.codes.ok:
            a = urlparse(url)
            fname = os.path.basename(a.path)
            with open(os.path.join(targetdir, fname), 'wb') as f:
                f.write(r.content)
    else:
        print("Broken dl request %s for %s" % (url, targetdir))



def write_ad(jad):
    target = os.path.join(archive_dir, jad["id"])

    stopwords = ["byggmax", "bauhaus", "storytel", "adlibris"]

    if any(stopword in jad["title"].lower() for stopword in stopwords):
        print("Skipping due to stopword for %s" % jad["id"])
        return

    # save ad files
    if not os.path.exists(target): 
        os.makedirs(target)
        filename = jad["id"]  + ".json"
        with open(os.path.join(target, filename), 'w') as outfile:
            json.dump(jad, outfile)

        # write media
        for item in jad["images"]:
            save_file(item, target)

        if "thumbnail" in jad.keys():
            save_file(jad["thumbnail"], target)

    else:
        # Files for this ad already saved
        print("Already saved files for %s" % jad["id"])



    # Save ad to db
    if session.query(Ad).filter_by(fbid=jad["id"]).count() == 0:
        print("Saving %s to database" % jad["id"])

        # clean targeting dupes
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
    else:
        print("Already in db %s" % jad["id"])


def get_pp_session():
    pp_sessionkey = os.environ["PP_SESSIONKEY"]
    return {"_fbpac-api_session":pp_sessionkey}



if __name__=="__main__":
    
    cookies = get_pp_session()

    parser = argparse.ArgumentParser()
    parser.add_argument("--list", help="Only list ads", action="store_true")
    parser.add_argument("--min", help="Min probapility", type=int)
    parser.add_argument("--max", help="Max probapility", type=int)
    parser.parse_args()
    args = parser.parse_args()

    if args.min and args.max:
        r = requests.get(f"https://projects.propublica.org/fbpac-api/ads?poliprob={args.min}&maxpoliprob={args.max}&lang=sv-SE", cookies=cookies)
        if r.status_code == requests.codes.ok:
            jdata = r.json()

            print("Found %s ads" % len(jdata["ads"]))
            print("Total adcount: %s" % jdata["total"])

            pages = math.ceil((jdata["total"]) / 20)
            print("Pages: %s" % pages)

            for page in range(0, pages):
                r = requests.get(f"https://projects.propublica.org/fbpac-api/ads?poliprob={args.min}&maxpoliprob={args.max}&page={page}&lang=sv-SE", cookies=cookies)
                if r.status_code == requests.codes.ok:
                    jdata = r.json()
                    for ad in jdata["ads"]:
                        ad = normalize_data(ad)
                        if args.list:
                            # only listing them to check
                            polprob = "%.2f" % ad["political_probability"]
                            print(str(ad["id"]).ljust(20, " ") + "\t" + polprob + "\t"  + ad["advertiser"][:20].ljust(20) + "\t" + ad["title"][:25])
                        else:
                            write_ad(ad)            
                            session.commit()

