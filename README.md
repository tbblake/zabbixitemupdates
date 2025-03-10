# Zabbix item update scripts
Scripts to update items with positional macros

update_item_names.py - given a template or host, will update all of the positional macros ($1, $2...) with the correct names from the item key

template_links.py - given a template or host will identify all templates it links too, and link to it

check.sql - used to identify all templates & hosts that have positional macros in the item names
