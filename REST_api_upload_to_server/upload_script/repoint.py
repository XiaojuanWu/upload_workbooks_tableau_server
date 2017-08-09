# -*- coding: utf-8 -*-

import publish
import tabcmd
import utils
import config
import os
import datetime
import zipfile
import time
import locale
import re


# this class is responsible for creating and repointing files for an advertiser
class Repoint(object):
    # this is run as soon as Repoint() is called
    def __init__(self, file_name, adv_dir, adv_name, port, to_publish=False, to_staging=False):
        # declare varibles
        self.file_name = file_name
        self.adv_dir = adv_dir
        self.adv_name = adv_name
        self.to_publish = to_publish
        self.to_staging = to_staging
        self.port = port
        self.files = []
        # split file name to see what extension is on the end
        self.file_ext = os.path.splitext(self.file_name)[1]
        # if the file is a packaged workbook use repoint_schema()
        if self.file_ext == '.twbx':
            self.repoint_schema(self.file_name, self.adv_dir, self.adv_name)
            self.workbook_name = self.file_name.split('_')[2]
        elif self.file_ext == '.tds':
            self.repoint_datasource(self.file_name, self.adv_dir)
            self.workbook_name = self.file_name

    # repoints twbx file

    def repoint_schema(self, file_name, adv_dir, adv_name):
        # start the timer
        start_time = time.time()
        if zipfile.is_zipfile(file_name):
            # extract the xml from the packaged file
            xml = utils.xfile.get_xml_from_archive(config.settings.template_dir + file_name)
        else:
            xml = utils.xfile.xml_open(config.settings.template_dir + file_name)
        # get the root of the xml to prepare it for parsing
        root = xml.getroot()
        # split the file name into parts so we know what kind of file it is
        file_name_parts = file_name.split('_')
        # create new file name
        new_file = adv_dir + '/' + file_name_parts[0] + '_' + file_name_parts[1] + '_' + file_name_parts[
            2] + '_' + adv_dir + '.twbx'
        new_file_name = os.path.basename(new_file)
        utils.write_log('output/run.log', new_file_name, print_log_value=False)

        # iterate over the datasource connections
        for connection in root.iter('connection'):
            class_type = connection.get('class')
            schema_type = connection.get('dbname')
            if class_type == 'redshift':
                pass
            elif class_type == 'mysql' and re.search(r'advertiser_[^\D.]+_tetris', schema_type):
                connection.set('port', self.port)
                connection.set('dbname', 'advertiser_' + adv_dir + '_tetris')
            elif file_name_parts[2] != 'Multiverse' and class_type == 'mysql':
                connection.set('port', self.port)
                connection.set('dbname', 'shared_tetris')
        utils.write_log('output/run.log', u' Schema changed to ' + ' advertiser_' + adv_dir + '_tetris for ' + new_file)
        utils.write_log('output/run.log', u' Port changed to ' + self.port + ' for ' + new_file)

        # save the new xml into a new packaged file at the new
        utils.xfile.save_into_archive(xml, config.settings.template_dir + file_name, 'output/uploaded_content/' + new_file)
        xml.write('output/unpackaged_content/' + new_file[:-1], encoding="utf-8", xml_declaration=True)
        # check if the file is TrafficQuality
        if file_name_parts[2] == 'TrafficQuality':
            # if so, update the links (see 'utils' for function)
            utils.update_tq_links('output/uploaded_content/' + new_file, adv_name)
            utils.update_tq_links('output/unpackaged_content/' + new_file, adv_name)
            utils.update_rs_datasources('output/uploaded_content/' + new_file, adv_dir)
            utils.update_rs_datasources('output/unpackaged_content/' + new_file, adv_dir)
            # check if the file is TableOfContents
        elif file_name_parts[2] == 'TableOfContents':
            # if so, update the links (see 'utils' for function)
            utils.update_toc_links('output/uploaded_content/' + new_file, adv_name)
            utils.update_toc_links('output/unpackaged_content/' + new_file, adv_name)
        else:
            utils.update_rs_datasources('output/uploaded_content/' + new_file, adv_dir)
            utils.update_rs_datasources('output/unpackaged_content/' + new_file, adv_dir)
        # stop the timer
        end_time = time.time()
        # how long did it take
        elapsed_time = end_time - start_time
        # send the data out to upload_time.csv
        utils.write_row('output/upload_times.csv', config.session_uuid, datetime.datetime.now(), self.adv_dir,
                        self.adv_name, new_file_name, file_name_parts[1], file_name_parts[2], 'repoint',
                        locale.format("%.2f", elapsed_time), 'success', config.settings.get_user)
        self.files.append(new_file)
        # check params to see if the user wants to publish the content
        # if self.to_publish is True:
        #     # start the timer
        #     start_time = time.time()
        #     if file_name_parts[2] == 'Sandbox':
        #         project = 'Sandbox'
        #     else:
        #         project = None
        #     # publish.publish_content_to_server_tabcmd(adv_dir, adv_name, 'output/uploaded_content/' + new_file, uploaded_file_name, 'Default')
        #     tabcmd.Tabcmd(to_stage=self.to_staging).login(adv_name)
        #     tabcmd.Tabcmd(to_stage=self.to_staging).publish('output/uploaded_content/' + new_file, uploaded_file_name, project=project)
        #     tabcmd.Tabcmd(to_stage=self.to_staging).logout()
        #     # print u' Successfully generated' + str(new_file)
        #     utils.write_log('output/run.log', u'  Successfully generated ' + str(new_file), print_log_value=True)
        #     # stop the timer
        #     end_time = time.time()
        #     # how long did it take
        #     elapsed_time = end_time - start_time
        #     # print u'' + locale.format("%.2f", elapsed_time) + " sec" + ' - ' + str(uploaded_file_name) + ' published to ' + adv_name
        #     # print u'  ──────────────────────────────────────────'
        #     utils.write_log('output/run.log', u'  ' + locale.format("%.2f", elapsed_time) + " sec" + ' - ' + str(uploaded_file_name) + ' published to ' + adv_name, print_log_value=True)
        #     print u'────────────────────────────────────────────'
        #     # send the data out to upload_time.csv
        #     utils.write_row('output/upload_times.csv', config.session_uuid, datetime.datetime.now(), self.adv_dir,
        #                     self.adv_name, new_file_name, file_name_parts[1], file_name_parts[2], 'publish',
        #                     locale.format("%.2f", elapsed_time), 'success', config.settings.get_user)

    # @property
    def get_repointed_files(self):
        return self.files

    # repoints .twb file
    # this is being depricated in favor of uploading as a .twbx like other content
    def repoint_sandbox(self, file_name, adv_dir, adv_name):
        # print u' ' + file_name
        utils.write_log('output/run.log', u' ' + file_name, print_log_value=True)
        # print u' Repointing Sandbox file'
        utils.write_log('output/run.log', u' Repointing Sandbox file', print_log_value=True)
        # start the timer
        start_time = time.time()
        # open the xml in the file (since it's not packaged)
        xml = utils.xfile.xml_open(config.settings.template_dir + file_name)

        # split the file name at '_'
        file_name_parts = file_name.split('_')
        # generate a new file name
        new_file = adv_dir + '/' + file_name_parts[0] + '_' + file_name_parts[1] + '_' + file_name_parts[
            2] + '_' + adv_dir + '.twbx'
        new_file_name = file_name_parts[0] + '_' + file_name_parts[1] + '_' + file_name_parts[
            2] + '_' + adv_dir + '.twbx'
        # write a new xml file with the changes that we made
        xml.write('output/uploaded_content/' + new_file, encoding="utf-8", xml_declaration=True)
        xml.write('output/unpackaged_content/' + new_file, encoding="utf-8", xml_declaration=True)
        utils.update_sandbox_links('output/uploaded_content/' + new_file, adv_name)
        utils.update_sandbox_links('output/unpackaged_content/' + new_file, adv_name)
        # print u' Successfully generated' + str(new_file)
        utils.write_log('output/run.log', u'  Successfully generated ' + str(new_file), print_log_value=True)
        utils.zip_twb('output/uploaded_content/' + adv_dir, new_file_name)
        # stop the timer
        end_time = time.time()
        # how long did it take
        elapsed_time = end_time - start_time
        # send the data out to upload_time.csv
        utils.write_row('output/upload_times.csv', config.session_uuid, datetime.datetime.now(), self.adv_dir, self.adv_name,
                        new_file_name, file_name_parts[1], file_name_parts[2], 'repoint',
                        locale.format("%.2f", elapsed_time), 'success', config.settings.get_user)
        # check params to see if the user wants to publish the content
        if self.to_publish is True:
            # start the timer
            start_time = time.time()
            # if so, use the publish function (see 'publish.py')
            publish.publish_content_to_server_restapi(adv_dir, adv_name, 'output/uploaded_content/' + new_file + 'x', file_name_parts[2], is_sandbox=True,
                                              is_tds=False, to_stage=self.to_staging)
            # stop the timer
            end_time = time.time()
            # how long did it take
            elapsed_time = end_time - start_time
            # send the data out to upload_time.csv
            utils.write_row('output/upload_times.csv', config.session_uuid, datetime.datetime.now(), self.adv_dir, self.adv_name,
                            new_file_name, file_name_parts[1], file_name_parts[2], 'publish',
                            locale.format("%.2f", elapsed_time), 'success', config.settings.get_user)

    # repoints .tds file
    def repoint_datasource(self, file_name, adv_dir):
        # print u' ' + file_name
        utils.write_log('output/run.log', u' ' + file_name, print_log_value=True)
        # start the timer
        start_time = time.time()
        # open the xml in the file (since it's not packaged)
        xml = utils.xfile.xml_open(config.settings.template_dir + file_name)
        # get the root of the xml to prepare it for parsing
        root = xml.getroot()
        # find 'connection' node (each .tds file only has one)
        connection = root.find('connection')
        # update the schema
        connection.set('dbname', 'advertiser_' + adv_dir + '_tetris')
        connection.set('port', self.port)
        # designate new file name/directory
        new_file = adv_dir + '/' + file_name
        # write a new xml file with the changes that we made
        xml.write('output/uploaded_content/' + new_file, encoding="utf-8", xml_declaration=True)
        xml.write('output/unpackaged_content/' + new_file, encoding="utf-8", xml_declaration=True)
        # print u' Successfully generated ' + str(new_file)
        utils.write_log('output/run.log', u'  Successfully generated ' + str(new_file), print_log_value=True)
        # stop the timer
        end_time = time.time()
        # how long did it take
        elapsed_time = end_time - start_time
        short_file_name = self.file_name.split('.')[0]
        # send the data out to upload_time.csv
        utils.write_row('output/upload_times.csv', config.session_uuid, datetime.datetime.now(), self.adv_dir,
                        self.adv_name, self.file_name, 'v1.00.0', short_file_name,
                        'repoint', locale.format("%.2f", elapsed_time), 'success', config.settings.get_user)
        # check params to see if the user wants to publish the content
        if self.to_publish is True:
            # start the timer
            start_time = time.time()
            # if so, use the publish function (see 'publish.py')
            publish.publish_content_to_server_restapi(adv_dir, self.adv_name, 'output/uploaded_content/' + new_file,
                                                      file_name, is_sandbox=True, is_tds=True, to_stage=self.to_staging)
            # stop the timer
            end_time = time.time()
            # how long did it take
            elapsed_time = end_time - start_time
            # send the data out to upload_time.csv
            utils.write_row('output/upload_times.csv', config.session_uuid, datetime.datetime.now(), self.adv_dir, self.adv_name,
                            self.file_name, 'v1.00.0', short_file_name, 'publish', locale.format("%.2f", elapsed_time),
                            'success', config.settings.get_user)
