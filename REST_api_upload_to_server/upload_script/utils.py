# -*- coding: utf-8 -*-

from tableaudocumentapi import Workbook
from tableaudocumentapi import xfile
from tableaudocumentapi import Datasource
import config
import publish
from Naked.toolshed.shell import execute_rb
import zipfile
import psycopg2
import re
import os
import csv
import glob
import shutil
import datetime
from collections import defaultdict
import numpy as np
import pandas as pd


# grabs the unique id from the Tableau Server
def get_content_id(adv_name, project=None, workbook=None):
    # set query variables, must pass in either a project or workbook name
    project_query = "SELECT p.id\
                    FROM _sites s\
                    LEFT JOIN _projects p ON p.site_id = s.id\
                    LEFT JOIN _workbooks w ON w.site_id = s.id\
                    WHERE w.name is not null and s.url_namespace = '{}' and p.name = '{}'\
                    GROUP BY p.id".format(adv_name, project)
    workbook_query = "SELECT w.id\
                    FROM _sites s LEFT JOIN _workbooks w ON w.site_id = s.id\
                    WHERE w.name is not null and s.url_namespace = '{}' and w.name = '{}'".format(adv_name, workbook)
    # determine the type of query to run
    if project is not None and workbook is None:
        # run query to get project id
        project_id = execute_query(project_query)
        # return results as a string
        return str(project_id)

    elif project is None and workbook is not None:
        # run query to get workbook id
        workbook_id = execute_query(workbook_query)
        # return results as a string
        return str(workbook_id)
    # otherwise raise a TypeError
    else:
        raise TypeError('must enter either a project or workbook name as a parameter')


# takes a workbook id and returns a workbook name
def reverse_lookup(workbook_id):
    reverse_lookup_query = "SELECT w.name FROM _workbooks w WHERE w.id = {}".format(workbook_id)
    # execute the query
    lookup = execute_query(reverse_lookup_query)
    return lookup


def execute_query(query):
    # Where are we connecting
    conn_string = config.settings.get_pg_conn
    # get a connection, if a connection cannot be made an exception will be raised here
    conn = psycopg2.connect(conn_string)
    # conn.cursor will return a cursor object, you can use this cursor to perform the desired query
    cursor = conn.cursor()
    # execute Query
    cursor.execute(query)
    # retrieve the records from the database (limit to 1 row)
    rows = cursor.fetchone()
    results = rows[0]
    return results


def update_tq_links(file_name, adv_name):
    if zipfile.is_zipfile(file_name):
        # extract the xml from the packaged file
        xml = xfile.get_xml_from_archive(file_name)
    else:
        xml = xfile.xml_open(file_name[:-1])
    # get the root of the xml to prepare it for parsing
    root = xml.getroot()
    # iterate over the root
    for child in root:
        # find all instances of the node 'zone'
        for zone in child.iter('zone'):
            # get the attribute 'url'
            url = zone.get('url')
            # only focus on those nodes that have the attribute
            if url is not None:
                # break up the url on '/'
                url_split = url.split('/')
                # update the adv_name in the url
                url_split[5] = adv_name
                # build url (see function)
                new_url = build_url(url_split)
                # set the 'url' property to the new url
                zone.set('url', new_url)
    if zipfile.is_zipfile(file_name):
        # save updated xml back into the zipped file
        xfile.save_into_archive(xml, file_name)
        # print u" Links for " + file_name + " repointed"
        write_log('output/run.log', u"  Links for " + file_name + " repointed", print_log_value=False)
    else:
        xml.write(file_name[:-1], encoding="utf-8", xml_declaration=True)


def update_toc_links(file_name, adv_name):
    if zipfile.is_zipfile(file_name):
        # extract the xml from the packaged file
        xml = xfile.get_xml_from_archive(file_name)
    else:
        xml = xfile.xml_open(file_name[:-1])
    # get the root of the xml to prepare it for parsing
    root = xml.getroot()
    # iterate over the child nodes
    for child in root:
        # find all instances of the node 'zone'
        for zone in child.iter('zone'):
            # get the attribute 'url'
            url = zone.get('url')
            # only focus on those nodes that have the attribute
            if url is not None:
                # break up the url on '/'
                url_split = url.split('/')
                # determine what the url links to and rebuild it
                try:
                    if url_split[6] == 'workbooks':  # individual workbooks
                        url_split[5] = adv_name
                        workbook_name = reverse_lookup(url_split[7])
                        new_workbook_id = get_content_id(adv_name, project=None, workbook=workbook_name)
                        url_split[7] = new_workbook_id
                        new_url = build_url(url_split)
                        zone.set('url', new_url)
                    elif url_split[6] == 'views':  # all views
                        url_split[5] = adv_name
                        new_url = build_url(url_split)
                        zone.set('url', new_url)
                    elif url_split[3] == 't':  # sandbox web edit
                        url_split[4] = adv_name
                        new_url = build_url(url_split)
                        zone.set('url', new_url)
                    elif url_split[6] == 'projects':  # sandbox views
                        url_split[5] = adv_name
                        url_split[7] = get_content_id(adv_name, project='Sandbox')
                        new_url = build_url(url_split)
                        zone.set('url', new_url)
                # if TypeError, then build a url that links to all views
                except TypeError:
                    url_split[5] = adv_name
                    new_url = build_url(url_split)
                    zone.set('url', new_url)
    if zipfile.is_zipfile(file_name):
        # save updated xml back into the zipped file
        xfile.save_into_archive(xml, file_name)
        # print u" Links for " + file_name + " repointed"
        write_log('output/run.log', u" Links for " + file_name + " repointed", print_log_value=False)
    else:
        xml.write(file_name[:-1], encoding="utf-8", xml_declaration=True)


def update_rs_datasources(file_name, adv_id):
    if zipfile.is_zipfile(file_name):
        # extract the xml from the packaged file
        xml = xfile.get_xml_from_archive(file_name)
    else:
        xml = xfile.xml_open(file_name[:-1])
    # get the root of the xml to prepare it for parsing
    root = xml.getroot()
    for items in root:
        for conn in items.iter('relation'):
            connection = conn.get('connection')
            if re.search('redshift', str(connection)):
                # Update redshift connections
                find_client_ref_id = re.compile(r'client_ref_id\s?=\s?\d+')
                find_advertiser_id = re.compile(r'advertiser_id\s?=\s?\d+')
                # handle MIDemo account
                if adv_id == '999999':
                    new_query = find_client_ref_id.sub('client_ref_id = 877', conn.text)
                    new_query_2 = find_advertiser_id.sub('advertiser_id = 877', new_query)
                else:
                    new_query = find_client_ref_id.sub('client_ref_id = ' + adv_id, conn.text)
                    new_query_2 = find_advertiser_id.sub('advertiser_id = ' + adv_id, new_query)
                conn.text = new_query_2
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


def update_sandbox_links(file_name, adv_name):
    with open(file_name, 'rb+') as sandbox:
        data = sandbox.read()  # Open the file and read it to memory
        # finds the path for the advetiser site and replaces it in the two places
        new_data = re.sub(r"path='/t/\w+/", "path='/t/{}/".format(adv_name), data)
        replace1 = re.sub(r"path=\"/t/\w+/", "path=\"/t/{}/".format(adv_name), new_data)
        replace2 = re.sub(r"site='\w+'", "site='{}'".format(adv_name), replace1)
        replace3 = re.sub(r"site=\"\w+", "site=\"{}".format(adv_name), replace2)
        sandbox.seek(0)  # go to the beggning of the file
        sandbox.write(replace3)  # write new data
        sandbox.truncate()  # eliminate the old data
        sandbox.close()  # close the file


def prepare_datasources(xml_root):
    datasources = []
    datasource_elements = xml_root.find('datasources')
    # loop through xml to get a list of the datasources to be updated
    if datasource_elements is None:
        return []
    for datasource in datasource_elements:
        ds = Datasource(datasource)
        datasources.append(ds)
    return datasources


# grabs a list of connections for a workbook
def view_conn_info(adv_dir, file_name):
    source = Workbook(adv_dir + '/' + file_name)
    for ds in source.datasources:
        for conn in ds.connections:
            # print conn
            write_log('output/run.log', conn, print_log_value=True)


# builds a new url based on a list of parts that is passed into the function
def build_url(split_url):
    new_url = ''
    for part in split_url:
        if new_url == '':
            new_url = part
        else:
            new_url = new_url + '/' + part
    return new_url


# Confirm if a directory for a given id exists, if not, create it
def check_dir_exist(adv_dir):
    if os.path.exists(adv_dir) and not os.path.isdir(adv_dir):
        raise NameError(adv_dir + " exists, but is not a directory.")
    elif os.path.exists(adv_dir) and os.path.isdir(adv_dir):
        pass
    elif not os.path.exists(adv_dir):
        os.makedirs(adv_dir)
        # print u' Creating folder for ' + adv_dir
        write_log('output/run.log', u' Creating folder for ' + adv_dir)


# if new_file=False, add a row to the existing specified file, else create a new file
def write_row(out_file, upload_uuid, date, adv_id, adv_name, full_file_name, version, short_file_name, action,
              time_to_complete, status, user, new_file=False):
    with open(out_file, 'ab' if new_file is False else 'w') as time_file:
        writer = csv.writer(time_file)
        new_row = [upload_uuid, date, adv_id, adv_name, full_file_name, version, short_file_name, action,
                   time_to_complete, status, user]
        writer.writerow(new_row)


# get last row of a csv
def get_last_row(csv_file_name):
    with open(csv_file_name, 'rb') as fails:
        fail_list = fails.readlines()
        last_row = fail_list[len(fail_list) - 1]
        last_row_list = last_row.split(',')
        return last_row_list


def zip_twb(adv_dir, twb_file):
    file_name, file_ext = os.path.splitext(twb_file)
    temp_name = adv_dir + '/' + file_name + '.temp'
    os.mkdir(temp_name)
    os.rename(adv_dir + '/' + twb_file, temp_name + '/' + twb_file)
    # turn temp directory into an archive
    for name in glob.glob(adv_dir + '/' + '*temp'):
        file_name, file_ext = os.path.splitext(name)
        shutil.make_archive(file_name, 'zip', name)
        shutil.rmtree(name)
    # change the .zip extension to .twbx
    for name in glob.glob(adv_dir + '/' + '*.zip'):
        file_name, file_ext = os.path.splitext(name)
        # print u' ' + file_name + '.twb' + ' converted to .twbx'
        write_log('output/run.log', u' ' + file_name + '.twb' + ' converted to .twbx', print_log_value=True)
        os.rename(name, file_name + '.twbx')


def create_graphviz_files(pattern):
    check_dir_exist('output/graphviz_files/')
    for file_name in glob.glob(config.settings.template_dir + '*' + pattern + '*.twbx'):
        xml = xfile.get_xml_from_archive(file_name)
        twb_file_name = file_name[:-1]
        xml.write(twb_file_name, encoding="utf-8", xml_declaration=True)
        execute_rb('upload_script/gen_graphviz.rb', arguments=twb_file_name)
        os.rename(twb_file_name.split('/')[2] + '.dot', 'output/graphviz_files/' + twb_file_name.split('/')[2] + '.dot')
        os.remove(twb_file_name)
        return 'output/graphviz_files/' + twb_file_name.split('/')[2] + '.dot'


def retry_upload_failures(failure_list_csv):
    with open(failure_list_csv, 'rb') as retry_list:
        reader = csv.reader(retry_list)
        if get_last_row(failure_list_csv)[0] == str(config.session_uuid):
            # print u' Trying failed files a second time'
            write_log('output/run.log', u' Trying failed files a second time', print_log_value=True)
        else:
            # print u' No files failed to upload'
            write_log('output/run.log', u' No files failed to upload', print_log_value=True)
        for line in reader:
            if line[0] == str(config.session_uuid):
                # print u' Uploading ' + line[2] + '/' + line[4]
                write_log('output/run.log', u' Uploading ' + line[1], print_log_value=True)
                publish.publish_content_to_server_tabcmd(line[3], line[4], 'output/uploaded_content/' + line[1] + '/' + line[4], project=None)


def write_log(log_file, log_value, print_log_value=False, newln=True):
    if print_log_value:
        print log_value
    with open(log_file, 'a') as logfile:
        if newln:
            logfile.write(str(datetime.datetime.now()) + ' ' + log_value + '\n')
        else:
            logfile.write(str(datetime.datetime.now()) + ' ' + log_value)


def write_csv(csv_file, *args):
    with open(csv_file, 'wb') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(args)


def audit_wb_fields(outfile, *args):
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
        freq_df.sort(['frequency', 'field_name'], ascending=[False, True]).to_csv('sorted_freq.csv')
        with open('sorted_freq.csv', 'rb') as source:
            rdr = csv.reader(source)
            with open('Field_Frequency.csv', 'wb') as results:
                wtr = csv.writer(results)
                for row in rdr:
                    wtr.writerow((row[1], row[2]))
        os.remove('freqterms.csv')
        os.remove('sorted_freq.csv')


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
                        # column_value = columns.get('value')
                        if column_name is not None:
                            # print column_name, column_value
                            if column_name == 'Start Date':
                                columns.set('value', min_date.strftime("#%Y-%m-%d#"))
                                calc = columns.find('calculation')
                                calc.set('formula', min_date.strftime("#%Y-%m-%d#"))
                            elif column_name == 'End Date':
                                columns.set('value', max_date.strftime("#%Y-%m-%d#"))
                                calc = columns.find('calculation')
                                calc.set('formula', max_date.strftime("#%Y-%m-%d#"))
    if zipfile.is_zipfile(file_name):
        # save updated xml back into the zipped file
        xfile.save_into_archive(xml, file_name)
        # write_log('output/run.log', "  Links for " + file_name + " repointed", print_log_value=True)
    else:
        xml.write(file_name, encoding="utf-8", xml_declaration=True)
