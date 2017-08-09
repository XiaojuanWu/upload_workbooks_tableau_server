# -*- coding: utf-8 -*-

import subprocess
import re
from os import sys, path
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
import upload_script


def simple_test():
    print 'Required Packages:'

    print 'Checking for tableaudocumentapi...',
    try:
        import tableaudocumentapi
        print 'Passed'
    except ImportError:
        print 'Failed'

    print 'Checking for tableau_tools...',
    try:
        import tableau_tools
        print 'Passed'
    except ImportError:
        print 'Failed'
        print 'Checking for lmxl...',
        try:
            import lxml
            print 'Passed'
        except ImportError:
            print 'Failed'

    print 'Checking for tableausdk...',
    try:
        import tableausdk
        print 'Passed'
    except ImportError:
        print 'Failed'

    print 'Checking for psycopg2...',
    try:
        import psycopg2
        print 'Passed'
    except ImportError:
        print 'Failed'

    print 'Checking for sqlalchemy...',
    try:
        import sqlalchemy
        print 'Passed'
    except ImportError:
        print 'Failed'

    def checkstdout(cmd, pattern, message_pass):
        # print u'├ ' + cmd
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        for line in p.stdout.readlines():
            if re.search(pattern, line):
                print message_pass
    print 'Checking for twb ruby gem...',
    checkstdout('gem list', 'twb', 'Passed')

    print 'Database Connections:'
    print 'Testing Postgres connection...',
    try:
        upload_script.utils.execute_query('SELECT * FROM _sites')
        print 'Passed'
    except psycopg2.Error:
        print 'Failed'

    print 'Testing MySQL connection...',
    try:
        export_data = upload_script.export_data.ExportData(upload_script.config.settings.get_tbi_conn_string)
        export_data.import_upload_data(limit_rows=1)
        print 'Passed'
    except sqlalchemy.exc.SQLAlchemyError:
        print 'Failed'

simple_test()
