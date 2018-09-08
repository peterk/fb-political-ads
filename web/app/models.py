from flask_sqlalchemy import SQLAlchemy, BaseQuery
import os
import json  
from sqlalchemy.dialects.postgresql import JSON

db = SQLAlchemy()


class BaseModel(db.Model):
    """Base data model for all objects"""
    __abstract__ = True
    
    def __init__(self, *args):
         super().__init__(*args)


class Ad(BaseModel):
    """A Facebook ad"""
    __tablename__ = 'ad'
    id = db.Column(db.Integer, primary_key = True)
    fbid = db.Column(db.String(), unique=True)
    is_supressed = db.Column(db.Boolean)
    advertiser = db.Column(db.String())
    message = db.Column(db.String())
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)
    raw = db.Column(JSON)

    plaintext = db.Column(db.String())
    plaintarget = db.Column(db.String())

    def first_image(self):
        if self.raw["images"]:
            return self.raw["images"][0]
        else:
            return "https://www.politiskannonsering.se/static/fb_politiska_annonser_banner.jpg"

    def raw_html(self):
        return self.raw["html"]
    
    def raw_targeting(self):
        return self.raw["targetings"]
