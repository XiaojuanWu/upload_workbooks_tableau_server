# -*- coding: utf-8 -*-

import upload_script.utils
import argparse
import sys
import subprocess


if __name__ == '__main__':
    try:
        # set up the parser
        parser = argparse.ArgumentParser(description='Marketing Intelligence Content Management Script v1.1', version='1.1')
        parser.add_argument('-rp', '--repoint-port', action='store', type=int, dest='port',
                            help='Specifies the port to which the content will be repointed '
                                 'before upload. This also initiates the process for content to be repointed. '
                                 'Choices are currently limitied to 11107 and 11108.')
        parser.add_argument('-u', '--upload', action='store_true',
                            help='Uploads content to the sites specified in docs/advertiser.config.')
        parser.add_argument('-rs', '--record-stats', action='store_true', dest='record',
                            help='Records the statistics of what occured during execution. History can be found in '
                                 'tunebi_metastats.upload_stats. Records from last upload are in the output folder.')
        parser.add_argument('-g', '--graphviz', action='store_true',
                            help='Generates .dot files showing workbook > dashboard > datasource relationships. '
                                 'Files are found in output/graphviz_files.')
        parser.add_argument('-s', '--stage', action='store_true', dest='stage',
                            help='Uploads files to staging server specified in advertiser.config')
        parser.add_argument('-d', '--delete', action='store_true', dest='delete',
                            help='Instead of uploading selected files, they are deleted from the listed sites')
        args = parser.parse_args()

        port = str(args.port) if args.port else None
        upload = args.upload if args.upload else False
        record = args.record if args.record else False
        graphviz = args.graphviz if args.graphviz else False
        staging = args.stage if args.stage else False
        uploader = upload_script.upload_content
        logger = upload_script.utils

        if port is None and upload is False and record is False and graphviz is False:
            subprocess.call(['python', 'run.py', '-h'])
        else:
            uploader.start_upload(repoint_port=port, publish_content=upload, record_stats=record,
                                  generate_graphviz=graphviz, staging=staging)

    except KeyboardInterrupt:
        sys.stdout.flush()
        print u' The upload process has been manually quit'
        logger.write_log('output/run.py', ' The script was exited by keyboard interrupt')
