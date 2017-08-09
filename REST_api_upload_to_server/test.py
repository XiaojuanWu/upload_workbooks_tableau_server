# -*- coding: utf-8 -*-

import csv
from export_data import *
import xml.etree.ElementTree as ET
import shutil
import os
import zipfile
import glob
from utils import *
import repoint
import MySQLdb
import subprocess
from tabcmd import *
import config
import publish
import datetime
import export_data
import re
import datetime
from dateutil.relativedelta import relativedelta
import pprint
from Naked.toolshed.shell import execute_rb
import time
from collections import defaultdict
import numpy as np
import pandas as pd

# print get_last_row('failed_files.csv')[0]
# print file_len('failed_files.csv')

# export_data = ExportData(config.settings.get_tbi_conn_string)
# export_data.get_upload_data('upload_times.csv')
# export_data.clear_table()
# export_data.export_data()
# export_data.import_upload_data(limit_rows=1)


repoint_port = '11107'
publish_content = False
template = 'template/1693/MI_v2.04.2_TrafficQuality_1693.twbx'


def extract_xml(source, new_file):
    xml = xfile.get_xml_from_archive(source)
    xml.write(new_file, encoding="utf-8", xml_declaration=True)


def update_mv_datasources(file_name, adv_id):
    if zipfile.is_zipfile(file_name):
        # extract the xml from the packaged file
        xml = xfile.get_xml_from_archive(file_name)
    else:
        xml = xfile.xml_open(file_name[:-1])
    # get the root of the xml to prepare it for parsing
    root = xml.getroot()
    for connection in root.iter('connection'):
        class_type = connection.get('class')
        print 'class ' + class_type
        # connection.set('port', '5439')
        # connection.set('dbname', 'mvuniverse')
    for items in root:
        for conn in items.iter('relation'):
            connection = conn.get('connection')
            # print connection
            if re.search('redshift', str(connection)):
                # Update redshift connections
                find_client_ref_id = re.compile(r'client_ref_id\s?=\s?\d+')
                # handle MIDemo account
                if adv_id == '999999':
                    new_query = find_client_ref_id.sub('client_ref_id = 877', conn.text)
                else:
                    new_query = find_client_ref_id.sub('client_ref_id = ' + adv_id, conn.text)
                conn.text = new_query
            elif re.search('mysql', str(connection)):
                # update mysql connections
                find_advertiser_id = re.compile(r'advertiser_id\s?=\s?\d+')
                # handle MIDemo account
                if adv_id == '999999':
                    new_query = find_advertiser_id.sub('advertiser_id = 877', conn.text)
                else:
                    new_query = find_advertiser_id.sub('advertiser_id = ' + adv_id, conn.text)
                conn.text = new_query
    # write the file
    if zipfile.is_zipfile(file_name):
        # save updated xml back into the zipped file
        xfile.save_into_archive(xml, file_name)
        # print u" Links for " + file_name + " repointed"
        write_log('output/run.log', "  Links for " + file_name + " repointed", print_log_value=True)
    else:
        xml.write(file_name[:-1], encoding="utf-8", xml_declaration=True)


def get_filters(file_name):
    if zipfile.is_zipfile(file_name):
        # extract the xml from the packaged file
        xml = xfile.get_xml_from_archive(file_name)
    else:
        xml = xfile.xml_open(file_name)
    # get the root of the xml to prepare it for parsing
    root = xml.getroot()
    filter_dict = {}
    for items in root:
        # print items
        for dashboards in items.iter('dashboards'):
            for dashboard in dashboards.iter('dashboard'):
                dashboard_name = dashboard.get('name')
                # print dashboard_name
                quick_filter_dict = {}
                for quick_filter in dashboard.iter('column-instance'):
                    quick_filter_name = quick_filter.get('column')
                    quick_filter_dict[quick_filter_name[1:-1]] = 'quick filter string'
                parameter_dict = {}
                for layouts in dashboard.iter('devicelayout'):
                    layout_name = layouts.get('name')
                    if layout_name == 'Tablet':
                        for zones in layouts.iter('zone'):
                            params = zones.get('type')
                            param_type = zones.get('mode')
                            if params == 'paramctrl':
                                # print params
                                for param in zones.iter('run'):
                                    param_name = param.text[:-1]
                                    parameter_dict[param_name] = 'parameter ' + param_type
                filter_dict[dashboard_name] = quick_filter_dict, parameter_dict
    return filter_dict


def update_dates(file_name, min_date, max_date):
    if zipfile.is_zipfile(file_name):
        # extract the xml from the packaged file
        xml = xfile.get_xml_from_archive(file_name)
    else:
        xml = xfile.xml_open(file_name)
    # get the root of the xml to prepare it for parsing
    root = xml.getroot()
    for items in root:
        # print items
        for datasources in items.iter('datasources'):
            for datasource in datasources.findall('datasource'):
                datasource_name = datasource.get('name')
                datasource_conn = datasource.get('hasconnection')
                if datasource_name == 'Parameters' and datasource_conn == "false":
                    for columns in datasource:
                        column_name = columns.get('caption')
                        column_value = columns.get('value')
                        if column_name is not None:
                            print column_name, column_value
                            if column_name == 'Min_Date':
                                columns.set('value', min_date.strftime("#%Y-%m-%d#"))
                                calc = columns.find('calculation')
                                calc.set('formula', min_date.strftime("#%Y-%m-%d#"))
                            elif column_name == 'Max_Date':
                                columns.set('value', max_date.strftime("#%Y-%m-%d#"))
                                calc = columns.find('calculation')
                                calc.set('formula', max_date.strftime("#%Y-%m-%d#"))
    if zipfile.is_zipfile(file_name):
        # save updated xml back into the zipped file
        xfile.save_into_archive(xml, file_name)
        # print u" Links for " + file_name + " repointed"
        # write_log('output/run.log', "  Links for " + file_name + " repointed", print_log_value=True)
    else:
        xml.write(file_name, encoding="utf-8", xml_declaration=True)


# current = datetime.datetime.now()
# last_month = datetime.datetime.now() - relativedelta(months=1)
# for adv_name, adv_id in config.settings.get_upload_batch:
#     print adv_name, adv_id
#     # for workbook in config.settings.get_templates:
#     # workbook_name = os.path.basename(workbook).split('.')[0]
#     print 'Deleting Sandbox'
#     Tabcmd().login(adv_name)
#     Tabcmd().delete('Sandbox')
#     Tabcmd().logout()
# utils.write_csv('test.csv', 1, 2, 3, 4, 5, 6, 7, 8, 9)

def new_upload_order():
    for adv_name, adv_id in config.settings.get_upload_batch:
        print adv_name, adv_id
        adv_files = []
        print 'File Prep'
        print '---------------------------'
        for workbook in config.settings.get_templates:
            file_ext = os.path.splitext(workbook)[1]
            # print file_ext
            # TODO: Refactor repoint behavior to call individual methods
            repointer = repoint.Repoint(workbook, adv_id, adv_name, port=repoint_port, to_publish=publish_content)

            if file_ext == '.twbx':
                repointer.repoint_schema(workbook, adv_id, adv_name)
                # print repointer.get_repointed_files() '
        for workbook in adv_files:
            print 'Uploading ' + workbook
            server_filename = workbook.split('_')[2]
            publish.publish_content_to_server_tabcmd(adv_id, adv_name, 'output/uploaded_content/' + workbook,
                                                     server_filename, 'Default')
            print 'Upload attempt complete'

        # TODO: Move publishing outside of the Repoint class
        # TODO: Publish again after all of the files have been repointed
        print '---------------------------'
        print 'All files attempted'


def write_csv(csv_file, *args):
    with open(csv_file, 'a') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(args)

# publish.publish_content_to_server_tabcmd('1693', 'BetaTest', template, 'Engagement', 'Default')
# new_upload_order()
read_mysql = 'mysql+mysqldb://read_tableau:ypxViOdFuVjP1Y0y3LPi@p-iproxy01.use01.plat.priv:11107/'
views = [('log_created', 'log_conversions'), ('log_created', 'log_attributables'), ('attributed_created', 'log_attributions')]
# write_csv('tetris_counts.csv', 'advertiser', 'log_conversions', 'log_attributables', 'log_attributions')


def write_totals():
    for adv_name, adv_id in config.settings.get_upload_batch:
        print adv_name
        adv_row = list()
        adv_row.append(adv_name)
        for database in views:
            query = 'SELECT count(*) from %s' % (database)
            try:
                export_data = ExportData(read_mysql, 'advertiser_' + adv_id + '_tetris')
                adv_row.append(int(export_data.run_raw_sql(query)[0]))
            except:
                adv_row.append(0)
        row_totals = adv_row[1] + adv_row[2] + adv_row[3]

        with open('tetris_counts.csv', 'a') as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerow(adv_row)


def write_history(min_date, max_date):
    with open('historical_counts.csv', 'w') as csv_file:
        csv_writer = csv.writer(csv_file)
        headers = ['advertiser', 'advertiser_id', 'view', 'row_count', 'date']
        csv_writer.writerow(headers)
    for adv_name, adv_id in config.settings.get_upload_batch:
        for date, database in views:
            mysql_engine = create_engine(read_mysql + 'advertiser_' + adv_id + '_tetris')
            conn = mysql_engine.connect()
            results = conn.execute("SELECT count(*), extract(YEAR_MONTH FROM {0}) FROM {1} WHERE {0} BETWEEN '{2}' AND '{3}' GROUP BY 2 ORDER BY 2".format(date, database, min_date, max_date))
            for row in results:
                print adv_name, adv_id, database, row[0], row[1]
                write_csv('historical_counts.csv', adv_name, adv_id, database, row[0], datetime.datetime.strptime(str(row[1]), '%Y%m'))


def get_fields(outfile, *args):
    tag_dict = {}
    db_tags = {}
    dashboard_fields = {}
    with open('Field_Tags.csv', 'rU') as tag_doc:
        rdr = csv.reader(tag_doc)
        for row in rdr:
            tag_dict[row[0]] = row[1]
    # pprint.pprint(tag_dict)
    with open(outfile, 'a') as text_file:
        master_col_list = []
        for file_name in args:
            if zipfile.is_zipfile(file_name):
                # extract the xml from the packaged file
                xml = xfile.get_xml_from_archive(file_name)
            else:
                xml = xfile.xml_open(file_name)
            # get the root of the xml to prepare it for parsing
            root = xml.getroot()
            ws_data = dict()
            text_file.write('\n' + '------------ ' + file_name + '\n')
            # print '\n' + '------------ ' + file_name + '\n'
            for items in root:
                for worksheets in items.iter('worksheets'):
                    for worksheet in worksheets.iter('worksheet'):
                        worksheet_name = worksheet.get('name')
                        ds_names = dict()
                        ds_list = dict()
                        for datasource in worksheet.iter('datasource'):
                            ds_names[datasource.get('name')] = datasource.get('caption')
                        ds_names['Parameters'] = 'Parameters'
                        for data_dep in worksheet.iter('datasource-dependencies'):
                            data_dep_name = data_dep.get('datasource')

                            col_list = []
                            for column in data_dep.iter('column'):
                                column_name = column.get('name')
                                column_caption = column.get('caption')
                                if column_caption is None:
                                    column_caption = column_name[1:-1]
                                col_list.append(column_caption)
                            ds_list[ds_names[data_dep_name]] = col_list
                            master_col_list += col_list
                        ws_data[worksheet_name] = ds_list

                for windows in items.iter('windows'):
                    viz_data = defaultdict(list)
                    for window in windows.iter('window'):
                        window_name = window.get('name')
                        window_class = window.get('class')
                        if window_class == 'dashboard':
                            for viewpoint in window.iter('viewpoint'):
                                viewpoint_name = viewpoint.get('name')
                                viz_data[window_name].append(viewpoint_name)

                    final_data = defaultdict(list)
                    for dashboard in viz_data:
                        for worksheet in viz_data[dashboard]:
                            final_data[dashboard].append({worksheet: ws_data[worksheet]})
                    for dashboard in viz_data:
                        field_array = []

                        for worksheet in final_data[dashboard]:
                            # print worksheet
                            for datasource in worksheet:
                                # print worksheet[datasource]
                                for fields in worksheet[datasource]:
                                    # print worksheet[datasource][fields]
                                    for field in worksheet[datasource][fields]:
                                        field_array.append(field)
                        unique_fields = np.unique(np.array(field_array))
                        # print np.unique(np.array(field_array))
                        dashboard_fields[dashboard] = unique_fields

                    for dashboard in dashboard_fields:
                        tag_array = list()
                        for field in dashboard_fields[dashboard]:

                            if tag_dict[field] != 'None':
                                tag_array.append(tag_dict[field])
                        unique_tags = np.unique(np.array(tag_array))
                        # print unique_tags
                        db_tags[dashboard] = unique_tags.tolist()

                    # pprint.pprint(db_tags)
                    # print db_tags
                    with open('Dashboard_Tags.csv', 'w') as tag_file:
                        wtr = csv.writer(tag_file)
                        wtr.writerow(('report_name', 'tags'))
                        for key, value in db_tags.iteritems():
                            wtr.writerow((key, str(value)[1:-1]))
                            # print key, value
                    # Generate the audit file
                    for dashboard in final_data:
                        text_file.write(str(dashboard) + '\n')
                        for worksheets in final_data[dashboard]:
                            text_file.write(str(worksheets) + '\n')
        np_col_array = np.array(master_col_list)
        np_col_array_unique, counts = np.unique(np_col_array, return_counts=True)
        counts = np.array(counts)
        fields = np.array(np_col_array_unique)
        freq_array = np.column_stack((counts, fields))

        with open('freqterms.csv', 'w') as outfile:
            outfile.write('frequency,field_name\n')
            for row in freq_array.tolist():
                outfile.write(str(row).replace("'", "", 2).replace(' ', '', 1)[1:-1] + '\n')
        freq_df = pd.read_csv('freqterms.csv', delimiter=',', dtype={'frequency': int, 'field_names': str})
        freq_df.sort_values(['frequency', 'field_name'], ascending=[False, True]).to_csv('sorted_freq.csv')
        with open('sorted_freq.csv', 'rb') as source:
            rdr = csv.reader(source)
            with open('Field_Frequency.csv', 'wb') as results:
                wtr = csv.writer(results)
                for row in rdr:
                    wtr.writerow((row[1], row[2]))
        os.remove('freqterms.csv')
        os.remove('sorted_freq.csv')

# extract_xml('template/1693/MI_v2.04.1_Multiverse_1693.twbx', 'Multiverse.twb')

# get_fields('Field_Audit.txt', 'Traffic_Quality.twb', 'Multiverse.twb', 'Engagement.twb', 'UserAcquisition.twb', 'Retention.twb', 'LTV.twb', 'Re-Engagement.twb', 'ExecutiveSummary.twb')
write_history('2016-01-01', '2017-01-31')
# write_totals()


# extract_xml('template/1693/MI_v2.04.1_Multiverse_1693.twbx', 'MVtempSample.twb')
# extract_xml('output/uploaded_content/3964/MI_v2.05.0_TrafficQuality_3964.twbx', 'TQ3964.twb')
# print reverse_lookup('2573')
