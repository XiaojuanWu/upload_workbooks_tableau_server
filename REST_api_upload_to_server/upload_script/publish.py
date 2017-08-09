# -*- coding: utf-8 -*-

from tableau_tools.tableau_rest_api.tableau_rest_api_connection import *
from tableau_tools.logger import *
import utils
import config
import urllib
import locale
import urllib2
import datetime
import tabcmd
import re


def publish_content_to_server_restapi(adv_id, adv_name, upload_file, new_file_name, is_sandbox=False, is_tds=False, to_stage=False):
    utils.write_log('output/run.log', u' Preparing upload to Tune BI server via REST api...', print_log_value=True)
    # start the timer for an iteration in the main loop
    start_time = time.time()
    # declare a log file for the logging process
    logger = Logger('output/restapi.log')
    if to_stage:
        server = config.settings.get_staging_server
    else:
        server = config.settings.get_server
    # get the server creds from the Config class to set up a connection to the server
    rest = TableauRestApiConnection(server, config.settings.get_user, config.settings.get_pw, site_content_url=adv_name)
    # enable logging so we can get details on the upload process
    rest.enable_logging(logger)
    # declare the file we want to upload as file_path
    file_path = upload_file
    # count the number of tries it takes to get a file uploaded
    attempts = 1
    # this initiates a loop to upload to the server
    while True:
        # connect to the server
        rest.signin()
        # print u' Connected'
        utils.write_log('output/run.log', u' Connected', print_log_value=True)
        # means that we want to try to do the following code unless we get a HTTPError
        try:
            # is the file either the sandbox or sandboxdashboardelements?
            if is_sandbox is True:
                # create the sandbox project in case it has not been, if it already has, the existing remains
                rest.create_project('Sandbox')
                # get the sandbox project id
                sb_luid = rest.query_project_luid_by_name('Sandbox')
                # show the sandbox prohect id
                # print u' Sandbox project ID: ' + sb_luid
                utils.write_log('output/run.log', u' Sandbox project ID: ' + sb_luid,
                                print_log_value=True)
                # publish the sandbox
                # check if it's a datasource
                if is_tds is False:
                    rest.publish_workbook(file_path, new_file_name, sb_luid, overwrite=True,
                                          connection_username=config.settings.get_db_user,
                                          connection_password=config.settings.get_db_pw,
                                          save_credentials=True, show_tabs=True, check_published_ds=True)
                else:
                    rest.publish_datasource(file_path, new_file_name, sb_luid, overwrite=True,
                                            connection_username=config.settings.get_db_user,
                                            connection_password=config.settings.get_db_pw,
                                            save_credentials=True)
            # condition currently not a part of Tune BI, but this is what we'd use to upload datasources for workbooks
            # in the 'default' project
            elif is_sandbox is False and is_tds is True:
                # get the default project id
                def_luid = rest.query_project_luid_by_name('Default')
                # print u' Default project ID: ' + def_luid
                utils.write_log('output/run.log', u' Default project ID: ' + def_luid)
                # upload via REST api
                rest.publish_datasource(file_path, new_file_name, def_luid, overwrite=True,
                                        connection_username=config.settings.get_db_user,
                                        connection_password=config.settings.get_db_pw,
                                        save_credentials=True)
            # implies that both is_sandbox and is_tds are False
            else:
                # get the defaul project id
                def_luid = rest.query_project_luid_by_name('Default')
                # print u' Default project ID: ' + def_luid
                utils.write_log('output/run.log', u' Default project ID: ' + def_luid)
                # quote file path for use in request (can be removed)
                quoted_file_path = urllib.quote(file_path)
                # print u' Uploading', quoted_file_path + '...'
                utils.write_log('output/run.log', u' Uploading', quoted_file_path + '...')
                # upload via REST api
                rest.publish_workbook(quoted_file_path, new_file_name, def_luid, overwrite=True,
                                      connection_username=config.settings.get_db_user, connection_password=config.settings.get_db_pw,
                                      save_credentials=True)
            # stop the timer
            end_time = time.time()
            # check how long the upload took
            elapsed_time = end_time - start_time
            # display how long the upload took
            # print u'' + locale.format("%.2f", elapsed_time), "sec" + '-' + upload_file, 'published to', adv_name
            end_line = u'' + locale.format("%.2f", elapsed_time) + "sec" + '-' + upload_file + ' published to ' + adv_name
            print u'  ──────────────────────────────────────────'
            utils.write_log('output/run.log', end_line, print_log_value=True)
            print u'────────────────────────────────────────────'
        # unless there is an HTTPError
        except urllib2.HTTPError:
            time.sleep(5)
            # stop the timer
            end_time = time.time()
            # check how long the upload took
            elapsed_time = end_time - start_time
            # then add 1 to the 'attempts' counter
            attempts += 1
            # sign out
            rest.signout()
            utils.write_log('output/run.log', u' Disconnected', print_log_value=True)
            # go through the try statement again
            if attempts == 6:
                # print u'Reached maximum number of attempts, moving on to next file'
                utils.write_log('output/run.log', u'Reached maximum number of attempts, moving on to next file', print_log_value=True)
                full_file_name = os.path.basename(upload_file)
                upload_file_name_parts = os.path.basename(upload_file).split('_')
                utils.write_row('output/upload_times.csv', config.session_uuid, datetime.datetime.now(), adv_id, adv_name, full_file_name,
                                upload_file_name_parts[1], new_file_name, 'publish - REST', locale.format("%.2f", elapsed_time),
                                'failed', config.settings.get_user)
                utils.write_row('output/failed_files.csv', config.session_uuid, datetime.datetime.now(), adv_id, adv_name, full_file_name,
                                upload_file_name_parts[1], new_file_name, 'publish - REST', locale.format("%.2f", elapsed_time),
                                'failed', config.settings.get_user)
                break
            # let the user know that it didn't work and there was an HTTP error
            end_line = u"✗unable to upload due to HTTP error, retrying... attempt #", attempts
            # print u"unable to upload due to HTTP error, retrying... attempt #", attempts
            utils.write_log('output/run.log', end_line, print_log_value=True)
            continue
        # once we successfully upload, complete the loop and move on to the next file
        break


def publish_content_to_server_tabcmd(adv_id, adv_name, upload_file, new_filename, project, to_stage=False):
    start_time = time.time()
    file_name_parts = os.path.basename(upload_file).split('_')
    if re.search("tds", os.path.basename(upload_file)):
        server_name = os.path.basename(upload_file)
        version = "v1.00.0"
    else:
        server_name = file_name_parts[2]
        version = file_name_parts[1]
    tabcmd.Tabcmd(to_stage=to_stage).login(adv_name)
    # utils.write_log('output/run.log', '  Preparting ' + upload_file + ' for upload', print_log_value=True)
    # tabcmd.Tabcmd(adv_id=adv_id, to_stage=to_stage).publish(upload_file, new_filename, project=project)
    # utils.write_log('output/run.log', '  Uploading ' + upload_file, print_log_value=True)
    tabcmd.Tabcmd(adv_id=adv_id, to_stage=to_stage).publish(upload_file, new_filename, project=project)
    tabcmd.Tabcmd(to_stage=to_stage).logout()
    end_time = time.time()
    elapsed_time = end_time - start_time
    # print u' ' + locale.format("%.2f", elapsed_time), "sec" + '-' + upload_file, 'published to', adv_name
    end_line = u'  ' + str(locale.format("%.2f", elapsed_time)) + " sec " + '- ' + upload_file + ' published to ' + adv_name
    print u'  ──────────────────────────────────────────'
    utils.write_log('output/run.log', end_line, print_log_value=True)
    print u'────────────────────────────────────────────'
    utils.write_row('output/upload_times.csv', config.session_uuid, datetime.datetime.now(), adv_id,
                    adv_name, os.path.basename(upload_file), version, server_name, 'publish - tabcmd',
                    locale.format("%.2f", elapsed_time), 'success', config.settings.get_user)
