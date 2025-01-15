# Set up RSA keys
if [ ! -d ./app/certs ]; then
  mkdir ./app/certs
  openssl req -x509 -newkey rsa:4086 \
    -subj "/C=NL/ST=XXXX/L=XXXX/O=UvA/CN=localhost" \
    -keyout "./app/certs/priv.pem" \
    -out "./app/certs/pub.pem" \
    -days 3650 -nodes -sha256
fi

# Configure a password
if [ ! -f ./app/certs/password.txt ]; then
  echo "No password detected, configure a new password:"
  read password
  touch ./app/certs/password.txt
  echo "$password" > ./app/certs/password.txt
fi

# Build app
docker-compose -f docker-compose.yml -f docker-compose-check.yml build
