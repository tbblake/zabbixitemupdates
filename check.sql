SELECT
  h.host,
  i.name,
  i.key_,
  h.status
FROM
  hosts h
  JOIN items i ON h.hostid = i.hostid
WHERE
  i.flags=0
  AND i.name regexp "\\$[[:digit:]]"
  AND i.templateid IS NULL;
