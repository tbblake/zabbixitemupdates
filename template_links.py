import sys
import mysql.connector
import argparse

class Node:
	types=('HOST','HOST','','TEMPLATE')
	def __init__(self,name,type):
		self.name=name
		self.type=self.types[type]
		self.children=[]
	def add_child(self,cname):
		self.children.append(cname)
	def __str__(self,*i):
		if len(i) == 0:
			i=0
		else:
			i=i[0]
		o='\t'*i
		o+=self.name+'('+self.type+')\n'
		for c in self.children:
			o+=c.__str__(i+1)
		return o

parser = argparse.ArgumentParser()
parser.add_argument('-s',dest='host_name',required=True,help='host or template name')
args = parser.parse_args()

# database credentials
db_host='' # database hostname / ip
db_inst='' # zabbix database instance
db_user='' # database user
db_pass='' # database password
myDB=mysql.connector.connect(host=db_host,database=db_inst,user=db_user,password=db_pass)

def find_linked_templates(h,torf):
	# torf:
	# True  - Templates we're linked too
	# False - Templates/hosts linked too us

	if not torf:
		sql=f'''SELECT
		       h.host,
		       h.status,
		       t.host,
		       t.status
		from
		       hosts h
		       right join hosts_templates ht on h.hostid=ht.hostid
		       right join hosts t on ht.templateid=t.hostid
		where
		       t.host="{h}"
		order by
			h.host;'''
	else:
		sql=f'''SELECT
		       t.host,
		       t.status,
		       h.host,
		       h.status
		from
		       hosts h
		       left join hosts_templates ht on h.hostid=ht.hostid
		       left join hosts t on ht.templateid=t.hostid
		where
		       h.host="{h}"
		order by
			t.host;'''

	myCursor=myDB.cursor()
	myCursor.execute(sql)

	rows=myCursor.fetchall()

	if len(rows)>0:
		t=Node(rows[0][2],rows[0][3])
		for r in rows:
			r=find_linked_templates(r[0],torf)
			if r:
				t.add_child(r)
	else:
		t=None
	return t

def printTree(root, markerStr="+- ", levelMarkers=[]):
	emptyStr = " "*len(markerStr)
	connectionStr = "|" + emptyStr[:-1]

	level = len(levelMarkers)
	mapper = lambda draw: connectionStr if draw else emptyStr
	markers = "".join(map(mapper, levelMarkers[:-1]))
	markers += markerStr if level > 0 else ""
	if level==0:
		indent=''
	else:
		indent='\t'
	print(f"{indent}{markers}{root.name}({root.type})")

	for i, child in enumerate(root.children):
		isLast = i == len(root.children) - 1
		printTree(child, markerStr, [*levelMarkers, not isLast])
		
mark_str='+---> '
print('*** Templates linked:')
results=find_linked_templates(args.host_name,True)
printTree(results,markerStr=mark_str)
print()

print('*** Templates/hosts linked to:')
results=find_linked_templates(args.host_name,False)
printTree(results,markerStr=mark_str)
