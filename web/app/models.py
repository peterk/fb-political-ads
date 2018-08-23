from flask_sqlalchemy import SQLAlchemy
import os
import json  
from sqlalchemy.dialects.postgresql import JSON

db = SQLAlchemy()


class BaseModel(db.Model):
    """Base data model for all objects"""
    __abstract__ = True
    
    def __init__(self, *args):
         super().__init__(*args)

    #def __repr__(self):
    #    """Define a base way to print models"""
    #    return '%s(%s)' % (self.__class__.__name__, {
    #        column: value
    #        for column, value in self._to_dict().items()
    #        })   


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

    def raw_html(self):
        return self.raw["html"]
    
    def raw_targeting(self):
        return self.raw["targetings"]
