cd /app
PATH=$PATH:/home/app_user/.local/bin:/home/app_user/.local/lib/python3.7/site-packages
uwsgi --master --https 0.0.0.0:5000,certs/pub.pem,certs/priv.pem --wsgi-file app.py --callable app --processes 4 --threads 2
