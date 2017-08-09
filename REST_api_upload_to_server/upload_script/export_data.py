# -*- coding: utf-8 -*-

from sqlalchemy import *
from sqlalchemy.orm import *
import csv
import time
import sys
import utils


class ExportData(object):
    def __init__(self, mysql_conn_string, mysql_schema=None):
        self.engine = create_engine(mysql_conn_string + mysql_schema)
        self.conn = self.engine.connect()
        self.Session = sessionmaker()
        self.session = Session(bind=self.engine)
        self.metadata = MetaData()
        self.upload_times = Table('upload_stats', self.metadata,
                                  Column('upload_uuid', String),
                                  Column('date', DateTime),
                                  Column('adv_id', String),
                                  Column('adv_name', String),
                                  Column('full_file_name', String),
                                  Column('version', String),
                                  Column('short_file_name', String),
                                  Column('action', String),
                                  Column('sec_to_complete', Numeric),
                                  Column('status', String),
                                  Column('user', String),
                                  )
        self.upload_time_list = []
        self.rows = 0

    def get_upload_data(self, export_data_file):
        with open(export_data_file, 'rb') as upload_log:
            reader = csv.DictReader(upload_log)
            for row in reader:
                self.upload_time_list.append(row)
                time.sleep(0.01)
                self.rows += 1
                sys.stdout.write(u" %d records found    \r" % self.rows)
                sys.stdout.flush()

    def export_data(self):
        self.conn.execute(self.upload_times.insert(), self.upload_time_list)
        print u"%d records exported to tunebi_metastats" % self.rows

    def import_upload_data(self, columns=None, filters=None, limit_rows=None):
        self.conn.execute(self.upload_times.select(columns).where(filters).limit(limit_rows))

    def clear_table(self):
        # clear the table, leave the schema in tact
        d = self.upload_times.delete()
        self.conn.execute(d)
        # print u'upload_stats has been cleared with the schema left in tact'
        utils.write_log('output/run.log', u'upload_stats has been cleared with the schema left in tact', print_log_value=True)

    def run_raw_sql(self, query_string):
        rows = self.conn.execute(query_string)
        results = []
        for row in rows:
            results.append(row[0])
        return rows
