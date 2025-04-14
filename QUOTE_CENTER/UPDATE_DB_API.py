import UPDATE_DB_FUNC as UDF 
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask import jsonify, Flask, render_template_string
import os, sys, io 
from contextlib import redirect_stdout
import logging

def UPDATE_DB():
	FILE_PATH = r"Z:/業務部/業務一課/G-報價/1. 外銷/"
	COST = UDF.CALCULATE_FILE(FILE_PATH)
	SUMMARY = UDF.QUOTATION_ANALYZE(COST)
	return SUMMARY
if __name__ == '__main__':
	hello = UPDATE_DB()
