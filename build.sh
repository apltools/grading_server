# Build the app and the check image
podman compose -f docker-compose.yml -f docker-compose-check.yml build
