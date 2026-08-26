import os, paramiko
c=paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("103.91.205.39", username="root", password=os.environ["VPS_PW"], timeout=30, allow_agent=False, look_for_keys=False)
cmd = """cd /var/www/likes-auto; PYTHONPATH=/var/www/likes-auto python3 -c \"from db import list_cron_logs, connect; 
rows=list_cron_logs(25);
[print(dict(r)) for r in rows];
con=connect();
print('---jobs---');
[print(dict(r)) for r in con.execute('SELECT job, COUNT(*) c FROM cron_logs GROUP BY job ORDER BY c DESC')];
con.close()\""""
_,o,e=c.exec_command(cmd, timeout=60)
print(o.read().decode('utf-8','replace'))
print(e.read().decode('utf-8','replace'))
c.close()