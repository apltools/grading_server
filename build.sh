if [ ! -d ./app/certs ]; then
  mkdir ./app/certs
  openssl req -x509 -newkey rsa:4086 \
    -subj "/C=NL/ST=XXXX/L=XXXX/O=UvA/CN=localhost" \
    -keyout "./app/certs/priv.pem" \
    -out "./app/certs/pub.pem" \
    -days 3650 -nodes -sha256
fi

docker-compose -f docker-compose.yml -f docker-compose-check.yml build
