Minha VPS

76.13.225.77
ssh root@76.13.225.77
     2020Admin@123    

cd /var/www/apps/curso-flask
git pull
nano .env
APP_ENV=production
docker compose up -d --build
------------------------------