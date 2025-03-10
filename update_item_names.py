import json
import sys
import mysql.connector
import requests
import argparse
from tabulate import tabulate

from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

parser = argparse.ArgumentParser()
parser.add_argument('-r',dest='update_items',action='store_true',default=False,help='execute changes (only lists by default)')
parser.add_argument('-t',dest='template_name',required=True,help='template name')
args = parser.parse_args()
template_name=args.template_name

zabbix_url='' # url to api_jsonrpc.php
zabbix_authid='' # authid to use against the api

# database credentials
db_host='' # database hostname / ip
db_inst='' # zabbix database instance
db_user='' # database user
db_pass='' # database passwordtype=['host','host(disabled)','','template'] # translate the status field to type of host object

# select all items with their hosts that are:
#     "plain items" - flags=0 (a.k.a. not discovered)
#     have a matching substring in the h.host field "used to pick out template and/or hosts"
#     are not templated (templateid is NULL)
       #AND i.name LIKE "%$%"
sql=f'''SELECT h.hostid,
       h.host,
       i.itemid,
       i.name,
       i.key_,
       h.status
FROM   hosts h
       JOIN items i
         ON h.hostid = i.hostid
       AND i.flags=0
       AND i.name regexp "\\\$[[:digit:]]"
       AND h.host = "{template_name}"
       AND i.templateid IS NULL;'''

# connect to the database, and execute the above SQL
myDB=mysql.connector.connect(host=db_host,database=db_inst,user=db_user,password=db_pass)
myCursor=myDB.cursor()
myCursor.execute(sql)

row=myCursor.fetchone() # get the first row

if not row: # got 0 results
	print('*** no matching items found ***')
	sys.exit()

output_table=[]
while row is not None:
	[hostid,host,itemid,oldname,key,status]=row
	newname=oldname
	key_params_text=key[key.index('[')+1:-1] # extract params between []
	key_params=key_params_text.split(',') # split the params
	param_index=0
	for param in key_params: # rewrite each parameter
		param_index+=1
		newname=newname.replace('$'+str(param_index), param)
	output_table.append([type[status],host,oldname,newname,key])
	if args.update_items:
		api_call={
			"jsonrpc":"2.0",
			"method":"item.update",
			"params":{
				"itemid":itemid,
				"name":newname
			},
			"auth":zabbix_authid,
			"id":1
		}
		try:
			r=requests.post(zabbix_url,data=json.dumps(api_call),headers={'Content-Type':'application/json'},verify=False)
			if r.status_code==200:
				print("api result -",r.text)
			else:
				print(f'ERROR - status code {r.status_code} - {r.text}')
				sys.exit()
		except Exception as e:
			print(f'ERROR - {e}')
			sys.exit()

	row=myCursor.fetchone()
headers=["type","name","old item name","new item name","key"]
print(tabulate(output_table,headers=headers))
