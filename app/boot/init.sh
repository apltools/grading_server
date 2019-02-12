DOCKER_SOCKET=/var/run/docker.sock
DOCKER_GROUP=docker_host
REGULAR_USER=app_user

DOCKER_GID=$(stat -c '%g' ${DOCKER_SOCKET})
addgroup -g ${DOCKER_GID} ${DOCKER_GROUP}
addgroup ${REGULAR_USER} ${DOCKER_GROUP}
chown -R app_user:app_group /app

su - app_user -c 'sh /app/boot/runner.sh'
