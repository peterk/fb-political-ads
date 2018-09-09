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



def html2text(rawhtml):
    tree = html.fromstring(rawhtml)
    text = tree.text_content()
    text = text.replace("SpSonSsrSadS","")
    return text



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
        if len(jad["images"]) > 0:
            for item in set(jad["images"]):
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
        ad.plaintext = html2text(jad["html"])
        if jad["targeting"]:
            if len(jad["targeting"]) > 0:
                ad.plaintarget = html2text(jad["targeting"])

        session.add(ad)
    else:
        print("Already in db %s" % jad["id"])


def get_pp_session():
    pp_sessionkey = os.environ["PP_SESSIONKEY"]
    return {"_fbpac-api_session":pp_sessionkey}


def print_ad(ad):
    polprob = "%.2f" % ad["political_probability"]
    print(str(ad["id"]).ljust(20, " ") + "\t" + polprob + "\t"  + ad["advertiser"][:20].ljust(20) + "\t" + ad["title"][:25])


if __name__=="__main__":
    
    cookies = get_pp_session()

    parser = argparse.ArgumentParser()
    parser.add_argument("--list", help="Only list ads", action="store_true")
    parser.add_argument("--new", help="Exclude existing ads while listing", action="store_true")
    parser.add_argument("--min", help="Min probapility", type=int)
    parser.add_argument("--max", help="Max probapility", type=int)
    parser.add_argument("--only", help="Only ad matching id", type=int)
    parser.add_argument("--oc", help="Only ads containing string in name", default=[], nargs = '*')
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
            if args.only:
                print("Only fetching %s" % args.only)

            for page in range(0, pages):
                r = requests.get(f"https://projects.propublica.org/fbpac-api/ads?poliprob={args.min}&maxpoliprob={args.max}&page={page}&lang=sv-SE", cookies=cookies)
                if r.status_code == requests.codes.ok:
                    jdata = r.json()
                    skip_count = 0
                    for ad in jdata["ads"]:
                        ad = normalize_data(ad)
                        target = os.path.join(archive_dir, ad["id"])

                        if args.list:
                            if args.new:
                                if os.path.exists(target):
                                    skip_count += 1
                                    continue
                                else:
                                    print_ad(ad)
                            else:
                                print_ad(ad)

                        else:
                            if args.only:
                                if str(ad["id"]) == str(args.only):
                                    write_ad(ad)
                                    session.commit()
                                    print("Solo ad %s saved." % ad["id"])
                                    sys.exit()
                            elif len(args.oc) > 0:
                                if any(word in ad["title"] for word in args.oc):
                                    if os.path.exists(target):
                                        skip_count += 1
                                        continue
                                    else:
                                        print_ad(ad)
                                        write_ad(ad)            
                                        session.commit()
                                        print("Word found, ad %s saved." % ad["id"])
                            else:
                                if args.new:
                                    if os.path.exists(target):
                                        skip_count += 1
                                        continue
                                else:
                                    print_ad(ad)
                                    write_ad(ad)            
                                    session.commit()

                    
                    print("Skipped %s existing ads" % skip_count)

