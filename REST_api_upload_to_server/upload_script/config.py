# -*- coding: utf-8 -*-

import re
import os
import csv
import uuid

session_uuid = uuid.uuid1()


class Config(object):
    def __init__(self, upload_config_file, advertiser_list):
        # userid/passwd, and template files, will be populated from config file
        self.user = self.pw = self.db_user = self.db_pw = self.server = self.staging_server = self.wb_name = ''
        self.pg_user = self.pg_pw = self.pg_server = ''
        self.mv_user = self.mv_pw = ''
        self.tbi_conn_string = ''
        self.twbs = []
        self.twbxs = []
        self.tdss = []
        self.templates = []
        self.upload_batch = []
        self.get_config(upload_config_file)
        self.get_advertisers_to_upload(advertiser_list)
        self.template_dir = self.get_template_dir()

    def get_config(self, upload_config_file):  # read in userid, passwd, valid template, etc
        if not os.path.exists(upload_config_file):
            raise NameError("file " + upload_config_file + " does not exist")
        with open(upload_config_file, 'rb') as cf:
            for line in cf:
                # strip leading/trailing white spaces, and quote characters
                line = self.fixquote(line, '')
                # skip lines with '#' in front of them
                if not line or line[0] == '#':
                    continue
                m_lu = re.match(r'(login_user *= *)(.*)', line)
                m_lp = re.match(r'(login_pw *= *)(.*)', line)
                m_du = re.match(r'(db_username *= *)(.*)', line)
                m_dp = re.match(r'(db_password *= *)(.*)', line)
                m_sv = re.match(r'(server *= *)(.*)', line)
                m_ss = re.match(r'(staging_server *= *)(.*)', line)
                m_wb = re.match(r'(wb_name *= *)(.*)', line)
                m_pu = re.match(r'(pg_username *= *)(.*)', line)
                m_pp = re.match(r'(pg_password *= *)(.*)', line)
                m_ps = re.match(r'(pg_server *= *)(.*)', line)
                t_cs = re.match(r'(tbi_conn_string *= *)(.*)', line)
                m_mu = re.match(r'(mv_username *= *)(.*)', line)
                m_mp = re.match(r'(mv_password *= *)(.*)', line)

                if m_lu:
                    self.user = m_lu.group(2)
                    self.user = self.fixquote(self.user, '')
                elif m_lp:
                    self.pw = m_lp.group(2)
                    self.pw = self.fixquote(self.pw, '')
                elif m_du:
                    self.db_user = m_du.group(2)
                    self.db_user = self.fixquote(self.db_user, '')
                elif m_dp:
                    self.db_pw = m_dp.group(2)
                    self.db_pw = self.fixquote(self.db_pw, '')
                elif m_sv:
                    self.server = m_sv.group(2)
                    self.server = self.fixquote(self.server, '')
                elif m_ss:
                    self.staging_server = m_ss.group(2)
                    self.staging_server = self.fixquote(self.staging_server, '')
                elif m_wb:
                    self.wb_name = m_wb.group(2)
                    self.wb_name = self.fixquote(self.wb_name, '')
                elif m_pu:
                    self.pg_user = m_pu.group(2)
                    self.pg_user = self.fixquote(self.pg_user, '')
                elif m_pp:
                    self.pg_pw = m_pp.group(2)
                    self.pg_pw = self.fixquote(self.pg_pw, '')
                elif m_ps:
                    self.pg_server = m_ps.group(2)
                    self.pg_server = self.fixquote(self.pg_server, '')
                elif m_mu:
                    self.mv_user = m_mu.group(2)
                    self.mv_user = self.fixquote(self.mv_user, '')
                elif m_mp:
                    self.mv_pw = m_mp.group(2)
                    self.mv_pw = self.fixquote(self.mv_pw, '')
                elif t_cs:
                    self.tbi_conn_string = t_cs.group(2)
                    self.tbi_conn_string = self.fixquote(self.tbi_conn_string, '')

                else:
                    if line.endswith('.twb'):
                        self.twbs.append(line)
                        self.templates.append(line)
                    elif line.endswith('.twbx'):
                        self.twbxs.append(line)
                        self.templates.append(line)
                    elif line.endswith('.tds'):
                        self.tdss.append(line)
                        self.templates.append(line)
            if not self.user or not self.pw or not self.db_user or not self.db_pw or not self.wb_name:
                raise NameError(
                    "Please check the advertiser.config, at least one parm is not correct.")

    def get_advertisers_to_upload(self, advertiser_list):
        with open(advertiser_list, 'rb') as al:  # display a list of (adv_name, adv_id) tuples
            reader = csv.reader(al)
            for row in reader:
                name = row[0]
                adv_id = row[1]
                adv_info = (name, adv_id)
                self.upload_batch.append(adv_info)

    @property
    def get_twbs(self):
        return self.twbs  # Returns only a list of twbs to be uploaded

    @property
    def get_twbxs(self):
        return self.twbxs  # Returns only a list of twbxs to be uploaded

    @property
    def get_tdss(self):
        return self.tdss  # Returns only a list of tdss to be uploaded

    @property
    def get_user(self):
        return self.user  # Returns tune BI user name

    @property
    def get_pw(self):
        return self.pw  # Returns tune BI password

    @property
    def get_db_user(self):
        return self.db_user  # tableau user access to MySQL database

    @property
    def get_db_pw(self):
        return self.db_pw  # tableau pw for access to MySQL database

    @property
    def get_server(self):
        return self.server  # tune MI staging server

    @property
    def get_staging_server(self):
        return self.staging_server  # tune MI staging server

    @property
    def get_pg_user(self):
        return self.pg_user  # postgres username

    @property
    def get_pg_pw(self):
        return self.pg_pw  # postgres password

    @property
    def get_pg_server(self):  # postgres server address
        return self.pg_server

    @property
    def get_upload_batch(self):
        return self.upload_batch  # list of adv name and id pairs to upload content for

    @property
    def get_templates(self):
        return self.templates  # combined list of all content to be uploaded

    @property
    def get_pg_conn(self):
        pg_conn = "host='" + self.pg_server + "' dbname='workgroup' port='8060' user='" + self.pg_user + "' password='" + self.pg_pw + "'"
        return pg_conn  # build the connection string for psycopg2 since it cannot accept a tuple

    @property
    def get_tbi_conn_string(self):
        return self.tbi_conn_string

    @property
    def get_mv_user(self):
        return self.mv_user  # multiverse username

    @property
    def get_mv_pw(self):
        return self.mv_pw  # multiverse password

    @staticmethod
    def fixquote(a, q):  # strip leading/trailing white spaces, and quote characters
        a = a.strip()
        a = a.strip("'")
        a = a.strip('"')
        a = a.strip()
        a = q + a + q
        return a

    @staticmethod
    def get_template_dir():
        template_dir = next(os.walk('template/'))[1]
        return 'template/' + ''.join(template_dir) + '/'

settings = Config('docs/advertiser.config', 'docs/advertiser_batch.csv')
