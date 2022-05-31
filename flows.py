#!/usr/bin/env python3
import cloudgenix
import argparse
from cloudgenix import jd, jd_detailed
import cloudgenix_settings
import sys
import logging
import os
import datetime
import collections 
import csv
from csv import DictReader
import json
from datetime import datetime, timedelta




# Global Vars
TIME_BETWEEN_API_UPDATES = 60       # seconds
REFRESH_LOGIN_TOKEN_INTERVAL = 7    # hours
SDK_VERSION = cloudgenix.version
SCRIPT_NAME = 'CloudGenix: Example script: Flow Record'
SCRIPT_VERSION = "v1"

# Set NON-SYSLOG logging to use function name
logger = logging.getLogger(__name__)


####################################################################
# Read cloudgenix_settings file for auth token or username/password
####################################################################

sys.path.append(os.getcwd())
try:
    from cloudgenix_settings import CLOUDGENIX_AUTH_TOKEN

except ImportError:
    # Get AUTH_TOKEN/X_AUTH_TOKEN from env variable, if it exists. X_AUTH_TOKEN takes priority.
    if "X_AUTH_TOKEN" in os.environ:
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('X_AUTH_TOKEN')
    elif "AUTH_TOKEN" in os.environ:
        CLOUDGENIX_AUTH_TOKEN = os.environ.get('AUTH_TOKEN')
    else:
        # not set
        CLOUDGENIX_AUTH_TOKEN = None

try:
    from cloudgenix_settings import CLOUDGENIX_USER, CLOUDGENIX_PASSWORD

except ImportError:
    # will get caught below
    CLOUDGENIX_USER = None
    CLOUDGENIX_PASSWORD = None

def flows(cgx, site_name, circuit_name, days):
    site_id = None
    wan_id = None
    app_id2n = {}
    for app in cgx.get.appdefs().cgx_content['items']:
        app_id2n[app["id"]] = app["display_name"]
    
    for sites in cgx.get.sites().cgx_content['items']:
        if sites["name"] == site_name:
            site_id = sites['id']
    
    if not site_id:
        print("No site named " + str(site_name) + " found")
        return
    
    wan_id2n = {}
    for wan_int in cgx.get.waninterfaces(site_id=site_id).cgx_content['items']:
        wan_id2n[wan_int["id"]] = wan_int["name"]
        if wan_int["name"] == circuit_name:
            wan_id = sites['id']
    
    if circuit_name:
        if not wan_id:
            print("No WAN named " + str(circuit_name) + " found")
            return
    
    end = datetime.utcnow()
    start = end - timedelta(minutes=60)
    flow_records = []
    csv_columns = []
    times = 24 * int(days)
    if wan_id:
        print("Getting flows from " + site_name + " on " + circuit_name) 
    else:
        print("Getting flows from " + site_name) 
    for x in range(times):
        
        end_time = end.isoformat()[:-3]+'Z'
        start_time = start.isoformat()[:-3]+'Z'
        if wan_id:
            data = {"start_time":start_time,"end_time":end_time,"filter":{"site":[site_id],"waninterface":[wan_id]},"debug_level":"all"}
        else:
            data = {"start_time":start_time,"end_time":end_time,"filter":{"site":[site_id]},"debug_level":"all"}
        
        resp = cgx.post.monitor_flows(data).cgx_content['flows']
        flows = resp['items']
        if resp:
            flows = resp['items']
            for record in flows:
                for item in record.keys():
                    if item not in csv_columns:
                        csv_columns.append(item)
                try:
                    record["app_id"] = app_id2n[record["app_id"]]
                except:
                    pass
                
                try:
                    record["flow_start_time_ms"] = datetime.fromtimestamp(record["flow_start_time_ms"]/1000).strftime("%Y-%m-%d %H:%M:%S")
                    record["flow_end_time_ms"] = datetime.fromtimestamp(record["flow_end_time_ms"]/1000).strftime("%Y-%m-%d %H:%M:%S")
                except:
                    pass
                    
                try:
                    record["waninterface_id"] = wan_id2n[record["waninterface_id"]]
                except:
                    pass
                flow_records.append(record)
                
        else:
            print("Failed to get flows")
            return
        num = (x / times) * 100
        num = format(num, '.0f')
        print(str(num) + "% Complete")
        
        end = end - timedelta(minutes=60)
        start = end - timedelta(minutes=60) 
        
    updated_flow_records = []
    for row in flow_records:
        for key in csv_columns:
            if key not in row:
                row[key] = "N/A"
        updated_flow_records.append(row)
    
    csv_file = "flow_list.csv"

    with open(csv_file, 'w') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_columns)
        writer.writeheader()        
        for row in updated_flow_records:
            writer.writerow(row)
            
        print("Saved upgrade_list.csv file")
                                      
def go():
    ############################################################################
    # Begin Script, parse arguments.
    ############################################################################

    # Parse arguments
    parser = argparse.ArgumentParser(description="{0}.".format(SCRIPT_NAME))

    # Allow Controller modification and debug level sets.
    controller_group = parser.add_argument_group('API', 'These options change how this program connects to the API.')
    controller_group.add_argument("--controller", "-C",
                                  help="Controller URI, ex. "
                                       "Alpha: https://api-alpha.elcapitan.cloudgenix.com"
                                       "C-Prod: https://api.elcapitan.cloudgenix.com",
                                  default=None)
    controller_group.add_argument("--insecure", "-I", help="Disable SSL certificate and hostname verification",
                                  dest='verify', action='store_false', default=True)
    login_group = parser.add_argument_group('Login', 'These options allow skipping of interactive login')
    login_group.add_argument("--email", "-E", help="Use this email as User Name instead of prompting",
                             default=None)
    login_group.add_argument("--pass", "-PW", help="Use this Password instead of prompting",
                             default=None)
    debug_group = parser.add_argument_group('Debug', 'These options enable debugging output')
    debug_group.add_argument("--debug", "-D", help="Verbose Debug info, levels 0-2", type=int,
                             default=0)
    config_group = parser.add_argument_group('Config', 'These options change how the configuration is generated.')
    config_group.add_argument('--site', '-S', help='A site name', required=True)
    config_group.add_argument('--wan', '-W', help='A WAN Name', required=False, default=None)
    config_group.add_argument('--days', '-T', help='How many previous days', required=False, default=1)
    
    args = vars(parser.parse_args())
                             
    ############################################################################
    # Instantiate API
    ############################################################################
    cgx_session = cloudgenix.API(controller=args["controller"], ssl_verify=args["verify"])

    # set debug
    cgx_session.set_debug(args["debug"])

    ##
    # ##########################################################################
    # Draw Interactive login banner, run interactive login including args above.
    ############################################################################
    print("{0} v{1} ({2})\n".format(SCRIPT_NAME, SCRIPT_VERSION, cgx_session.controller))

    # login logic. Use cmdline if set, use AUTH_TOKEN next, finally user/pass from config file, then prompt.
    # figure out user
    if args["email"]:
        user_email = args["email"]
    elif CLOUDGENIX_USER:
        user_email = CLOUDGENIX_USER
    else:
        user_email = None

    # figure out password
    if args["pass"]:
        user_password = args["pass"]
    elif CLOUDGENIX_PASSWORD:
        user_password = CLOUDGENIX_PASSWORD
    else:
        user_password = None

    # check for token
    if CLOUDGENIX_AUTH_TOKEN and not args["email"] and not args["pass"]:
        cgx_session.interactive.use_token(CLOUDGENIX_AUTH_TOKEN)
        if cgx_session.tenant_id is None:
            print("AUTH_TOKEN login failure, please check token.")
            sys.exit()

    else:
        while cgx_session.tenant_id is None:
            cgx_session.interactive.login(user_email, user_password)
            # clear after one failed login, force relogin.
            if not cgx_session.tenant_id:
                user_email = None
                user_password = None

    ############################################################################
    # End Login handling, begin script..
    ############################################################################

    # get time now.
    curtime_str = datetime.utcnow().strftime('%Y-%m-%d-%H-%M-%S')

    # create file-system friendly tenant str.
    tenant_str = "".join(x for x in cgx_session.tenant_name if x.isalnum()).lower()
    cgx = cgx_session
    site_name = args['site']
    circuit_name = args['wan']
    flows(cgx, site_name, circuit_name, args['days'])
    # end of script, run logout to clear session.
    cgx_session.get.logout()

if __name__ == "__main__":
    go()