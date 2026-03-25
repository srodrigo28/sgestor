cat > ~/infra-proxy/conf/default.conf << 'EOF'
# ==========================================
# SITE 1 - PORTAL (COM SSL/CADEADO) 🔒
# ==========================================
server {
    listen 443 ssl;
    server_name 99dev.pro www.99dev.pro;

    # Certificado do SITE PRINCIPAL
    ssl_certificate /etc/letsencrypt/live/99dev.pro/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/99dev.pro/privkey.pem;

    location / {
        proxy_pass http://site1:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# ==========================================
# JAVA APP (COM SSL/CADEADO) 🔒
# ==========================================
server {
    listen 443 ssl;
    server_name java.99dev.pro;

    # Certificado do JAVA
    ssl_certificate /etc/letsencrypt/live/java.99dev.pro/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/java.99dev.pro/privkey.pem;

    location / {
        proxy_pass http://app-java:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# ==========================================
# API PRECIFEX / ATAS (HTTP - AGUARDANDO SSL)
# ==========================================
server {
    listen 80;
    server_name api.99dev.pro;

    # Pasta para validacao do Certbot (nao remova)
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        # Aponta para o Gunicorn no Host (Porta 5000)
        # IP 172.17.0.1 = Gateway do Docker para falar com o Host
        proxy_pass http://172.17.0.1:5000;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# ==========================================
# NOVO APP FLASK (HTTP - APP.99DEV.PRO)
# ==========================================
server {
    listen 80;
    server_name app.99dev.pro;

    location / {
        proxy_pass http://127.0.0.1:5050;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# ==========================================
# REDIRECIONAMENTO GERAL (Forca HTTPS) 🔄
# ==========================================
server {
    listen 80;
    server_name 99dev.pro www.99dev.pro java.99dev.pro;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}
EOF
