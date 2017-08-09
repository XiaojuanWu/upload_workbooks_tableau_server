# -*- coding: utf-8 -*-

import config
import utils
import subprocess
import re


class Tabcmd(object):
    def __init__(self, adv_name=None, adv_id=None, to_stage=False):
        self.adv_name = adv_name
        self.adv_id = adv_id
        if to_stage:
            self.server = config.settings.get_staging_server
        else:
            self.server = config.settings.get_server
        self.failed_files = []

    def login(self, adv_name):
        cmd = 'tabcmd.sh login -s "' + self.server + '" -t "' + adv_name + '" -u "' + config.settings.get_user + '" -p "' + config.settings.get_pw + '" -no-certcheck'
        utils.write_log('output/run.log', 'Logged into tabcmd')
        return self.runtabcmd(cmd, printerr=True)

    def publish(self, file_name, new_file_name, project=None):
        base_cmd = 'tabcmd.sh publish "' + file_name + '" -n "' + new_file_name + '"'
        cmd_opt = ' -o --timeout 3600 --save-db-password -no-certcheck'
        if project is not None:
            proj = ' --project "' + project + '"'
        else:
            proj = ""
        if re.search(r'Multiverse', file_name):
            db_user = ' --db-username "' + config.settings.get_mv_user + '"'
            db_pass = ' --db-password "' + config.settings.get_mv_pw + '"'
        else:
            db_user = ' --db-username "' + config.settings.get_db_user + '"'
            db_pass = ' --db-password "' + config.settings.get_db_pw + '"'

        cmd = base_cmd + db_user + db_pass + cmd_opt + proj

        utils.write_log('output/run.log', '  Publishing ' + file_name, print_log_value=False)
        return self.runtabcmd(cmd, printerr=True)

    def logout(self):
        cmd = 'tabcmd.sh logout'
        utils.write_log('output/run.log', 'Logged out of tabcmd')
        return self.runtabcmd(cmd, printerr=True)

    def delete(self, new_file_name, project=None):
        cmd_opt = ' --project "Sandbox" -no-certcheck'
        base_cmd = 'tabcmd.sh delete --workbook "' + new_file_name + '"'
        cmd = base_cmd + cmd_opt
        utils.write_log('output/run.log', '  Deleted ' + new_file_name, print_log_value=True)
        return self.runtabcmd(cmd, printerr=True)

    def runtabcmd(self, cmd, printerr=False):
        # run tableau command and display the output
        # print u'├ ' + cmd
        utils.write_log('output/tabcmd.log', cmd)
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        p.wait()
        for line in p.stdout.readlines():
            utils.write_log('output/tabcmd.log', line, newln=False)
            if printerr:
                if re.search(r'\*\*\*', line):
                    utils.write_log('output/run.log', '  tabcmd encountered an error - check tabcmd.log for details', print_log_value=True)
                    utils.write_log('output/run.log', line, print_log_value=False)
                    # utils.write_csv('output/uploaded_content/' + self.adv_id + '/tabcmd_failures.csv', config.session_uuid, file_name, new_file_name, self.adv_id, self.adv_name, cmd)
                    # TODO: Build out a way to have this error caught so that a failed command can be rerun
                    # file_name_info = (self.adv_id, self.adv_name, file_name, new_file_name)
                    # self.failed_files.append(file_name_info)
