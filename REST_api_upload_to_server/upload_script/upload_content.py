# -*- coding: utf-8 -*-

import config
import repoint
import utils
import publish
import export_data
import time
import os
import re
import locale
import datetime
import time
from dateutil.relativedelta import relativedelta


def start_upload(repoint_port=None, publish_content=False, record_stats=False, generate_graphviz=False, staging=False):
    print u'────────────────────────────────────────────'
    time_log = {}
    utils.write_log('output/run.log', 'Session Settings:', print_log_value=True)
    # start the timer for the overall process
    start_time = time.time()
    # create upload times file with headers, clear data from last upload if file already exists
    utils.check_dir_exist('output')
    utils.write_row('output/upload_times.csv', 'upload_uuid', 'date', 'adv_id', 'adv_name', 'full_file_name', 'version',
                    'short_file_name', 'action', 'sec_to_complete', 'status', 'user', new_file=True)
    # bring in both configuration files to this module
    if repoint_port is not None:
        # print u' Advertisers repointing to ' + repoint_port
        utils.write_log('output/run.log', u' Advertisers repointing to ' + repoint_port, print_log_value=True)
        # print u' With ' + config.settings.template_dir + u' as template directory'
        utils.write_log('output/run.log', u' With ' + config.settings.template_dir + u' as template directory', print_log_value=True)
    if publish_content is True:
        # print u' Publishing to sites:'
        utils.write_log('output/run.log', u' Publishing to sites:', print_log_value=True)
        for adv_name, adv_id in config.settings.get_upload_batch:
            # print u' ' + adv_name + ' - ' + adv_id
            utils.write_log('output/run.log', u' ' + adv_name + ' - ' + adv_id, print_log_value=True)
        utils.write_log('output/run.log', u' On server:', print_log_value=True)
        if staging:
            utils.write_log('output/run.log', config.settings.get_staging_server, print_log_value=True)
        else:
            utils.write_log('output/run.log', config.settings.get_server, print_log_value=True)
    if record_stats is True:
        # print u' Recording stats on tunebi_metastats.upload_stats'
        utils.write_log('output/run.log', u' Recording stats on tunebi_metastats.upload_stats', print_log_value=True)
    if generate_graphviz is True:
        # print u' Saving graphviz files in output/graphviz_files'
        utils.write_log('output/run.log', u' Saving graphviz files in output/graphviz_files', print_log_value=True)

    # print u' Session UUID:' + str(config.session_uuid)
    utils.write_log('output/run.log', u' Session UUID:' + str(config.session_uuid), print_log_value=False)

    if repoint_port is not None:
        # this loop will generate the content
        for adv_name, adv_id in config.settings.get_upload_batch:
            rp_start_time = time.time()
            # use function from utils.py to check to see if the adv_id dir exists
            # print u' ' + adv_name + '-' + adv_id
            print u'────────────────────────────────────────────'
            utils.write_log('output/run.log', u' ' + adv_name + '-' + adv_id, print_log_value=True)
            print u'────────────────────────────────────────────'
            utils.check_dir_exist('output/uploaded_content/' + adv_id)
            utils.check_dir_exist('output/unpackaged_content/' + adv_id)
            # loop over list of content in advertiser.config to repoint and upload

            upload_order(repoint_port, publish_content)

            rp_end_time = time.time()
            rp_elapsed_time = rp_end_time - rp_start_time
            # if publish_content is False:
            #     print u' ' + str(rp_elapsed_time) + ' seconds elapsed'
            utils.write_log('output/run.log', u' ' + str(rp_elapsed_time) + ' seconds elapsed for ' + adv_name, print_log_value=True)
            time_log[adv_name] = rp_elapsed_time
            print u'────────────────────────────────────────────'
    elif repoint_port is None and publish_content is True:
        for adv_name, adv_id in config.settings.get_upload_batch:
            for workbook in config.settings.get_templates:
                file_name_parts = workbook.split('_')
                if re.search("tds", workbook):
                    adv_file_name = workbook
                else:
                    adv_file_name = file_name_parts[0] + '_' + file_name_parts[1] + '_' + file_name_parts[2] + '_' + adv_id + '_' + file_name_parts[4]
                if re.search("Sandbox", adv_file_name):
                    project = 'Sandbox'
                else:
                    project = None

                if os.path.exists('output/uploaded_content/' + adv_id + '/' + adv_file_name):
                    publish.publish_content_to_server_tabcmd(adv_id, adv_name, 'output/uploaded_content/' + adv_id + '/' + adv_file_name, project=project, to_stage=staging)
                else:
                    # print u' ' + adv_file_name + u' could not be uploaded because it does not exist'
                    utils.write_log('output/run.log', u' ' + adv_file_name + u' could not be uploaded because it does not exist', print_log_value=True)
        # print u'All files for ' + adv_name + ' successfully uploaded'
        utils.write_log('output/run.log', u'All files for ' + adv_name + ' successfully uploaded', print_log_value=True)
    if generate_graphviz is True:
        # print u" Generating graphviz files for content in template directory"
        utils.write_log('output/run.log', u" Generating graphviz files for content in template directory", print_log_value=True)
        for workbook in ['LTV', 'Engagement', 'Re-Engagement', 'UserAcquisition', 'TrafficQuality', 'Retention',
                         'ExecutiveSummary']:
            gv_start_time = time.time()
            graphviz_file = utils.create_graphviz_files(workbook)
            file_name_parts = os.path.basename(graphviz_file).split('_')
            # print u" " + graphviz_file
            utils.write_log('output/run.log', u" " + graphviz_file, print_log_value=True)
            gv_end_time = time.time()
            gv_elapsed_time = gv_end_time - gv_start_time
            utils.write_row('output/upload_times.csv', config.session_uuid, datetime.datetime.now(), file_name_parts[3],
                            'template', os.path.basename(graphviz_file), file_name_parts[1], file_name_parts[2],
                            'graphviz', locale.format("%.2f", gv_elapsed_time), 'success', config.settings.get_user)
        # print u" Graphviz files generated"
        utils.write_log('output/run.log', u" Graphviz files generated", print_log_value=True)

    if record_stats is True:
        # export to MySQL
        record_data = export_data.ExportData(config.settings.get_tbi_conn_string)
        record_data.get_upload_data('output/upload_times.csv')
        record_data.export_data()

    # stop the timer
    end_time = time.time()
    # determine how long the overall process took
    elapsed_time = end_time - start_time
    # display how long it took to upload all advertisers
    # print u'' + str(elapsed_time) + ' seconds elapsed in total'
    print 'Summary:'
    for adv in time_log:
        print " " + adv + " - " + str(time_log[adv]) + " sec"
    utils.write_log('output/run.log', u'' + str(elapsed_time) + ' seconds elapsed in total', print_log_value=True)


def upload_order(repoint_port, publish_content):
    cur_date = datetime.datetime.today()
    cur_day = cur_date.day
    if cur_day <= 20:
        cur_date = cur_date - relativedelta(months=1)
    else:
        cur_date = cur_date
    
    cur_day = cur_date.day
    cur_month = cur_date.month

    num_adv_to_upload = len(config.settings.get_upload_batch)
    num_adv_uploaded = 0
    
    for adv_name, adv_id in config.settings.get_upload_batch:
        num_adv_uploaded += 1
        print adv_name, adv_id
        adv_files = []
        print 'File Prep'
        print '---------------------------'
        for workbook in config.settings.get_templates:
            file_ext = os.path.splitext(workbook)[1]
            # print file_ext
            # TODO: Refactor repoint behavior to call individual methods
            repointer = repoint.Repoint(workbook, adv_id, adv_name, port=repoint_port, to_publish=False)
            if file_ext == '.twbx':
                repointer.repoint_schema(workbook, adv_id, adv_name)
                # TODO: Update to show first last day of previous month
                if cur_month in (1,3,5,7,8,10,12):
                	utils.update_dates('output/uploaded_content/' + repointer.get_repointed_files()[0], cur_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0), cur_date.replace(day=31, hour=0, minute=0, second=0, microsecond=0))
                elif cur_month == 2:
                	utils.update_dates('output/uploaded_content/' + repointer.get_repointed_files()[0], cur_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0), cur_date.replace(day=28, hour=0, minute=0, second=0, microsecond=0))
            	else:
            		utils.update_dates('output/uploaded_content/' + repointer.get_repointed_files()[0], cur_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0), cur_date.replace(day=30, hour=0, minute=0, second=0, microsecond=0))
                # print repointer.get_repointed_files()
                adv_files.append(repointer.get_repointed_files()[0])
                # TODO: Publish once after repoint
                print 'Preparing ' + repointer.get_repointed_files()[0]

        if publish_content:
            print 'Upload'
            num_files_to_upload = len(adv_files)
            print '---------------------------'
            num_files_uploaded = 0
            for workbook in adv_files:
                num_files_uploaded += 1
                print 'Uploading ' + workbook
                server_filename = workbook.split('_')[2]
                publish.publish_content_to_server_tabcmd(adv_id, adv_name, 'output/uploaded_content/' + workbook,
                                                         server_filename, 'Default')
                print 'Upload attempt complete'
                if num_files_uploaded <= num_files_to_upload:
                    time.sleep(20)

            # TODO: Move publishing outside of the Repoint class
            # TODO: Publish again after all of the files have been repointed
            print '---------------------------'
            print 'All files attempted'
            # print 'Waiting 2 min for next advertiser'
            #if num_files_uploaded <= num_adv_to_upload:
                #---------------------time.sleep(120)
