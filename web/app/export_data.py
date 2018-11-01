# make export file
import argparse
import json
import os
import sys
from models import Ad
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from lxml import html
from lxml.etree import tostring
from openpyxl import Workbook

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


def export(exportfilepath, exclude_media=True):
    """Export all ads and media files to zip file.

    :exportfilepath: Output path
    :returns: Number of exported ads.

    """

    ads = session.query(Ad).all() #.order_by(Ad.created_at)

    raw_data = []
    for ad in ads:
        raw_data.append(ad.raw)

    print("Done preparing. Writing...")
    
    with open(os.path.join(exportfilepath, "raw_data.json"), "w") as exportfile:
        # 1. raw data
        json.dump(raw_data, exportfile, sort_keys=True, indent=4, ensure_ascii=False)

        # 2. ad_targets.xlsx
        make_targets_xlsx(raw_data, exportfilepath)


def get_target(targets, target_key):
    if targets:
        for target in targets:
            if target.get("target") == target_key:
                return target["segment"]
    else:
        return ""


def html2text(rawhtml):
    text = ""
    if rawhtml:
        tree = html.fromstring(rawhtml)
        text = tree.text_content()
    return text


def make_targets_xlsx(raw_data, exportfilepath):

    wb = Workbook()
    ws = wb.active

    #header
    ws.append(["id", "advertiser", "title", "lower_page", "message", "political_probability", "Segment", "Age", "MinAge", "State", "City", "Gender", "Retargeting"])

    for ad in raw_data:
        row = []
        row.append(ad["id"])
        row.append(ad["advertiser"])
        row.append(ad["title"])
        row.append(ad["lower_page"])
        row.append(html2text(ad["message"]))
        row.append(ad["political_probability"])

        target_keys = ["Segment", "Age", "MinAge", "State", "City", "Gender", "Retargeting"]

        for key in target_keys:
                row.append(get_target(ad["targets"], key))

        ws.append(row)

    wb.save(os.path.join(exportfilepath, "ad_targets.xlsx"))





if __name__=="__main__":

    # write the following files:
    #
    # 1. raw_data.json - JSON data as received from the propublica database
    # 2. ad_targets.xlsx
    
    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="Export file name")

    args = parser.parse_args()
    exportfilepath = args.filename
    print("Exporting to %s" % exportfilepath)

    if not os.path.exists(exportfilepath):
        os.makedirs(exportfilepath)

    export(exportfilepath)
