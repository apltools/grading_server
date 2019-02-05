if [[ "$(docker container ls -aqf grading_server_scheduler 2> /dev/null)" == "" ]]; then
  docker run -d -t -v /var/run/docker.sock:/var/run/docker.sock -p 5000:80 --name scheduler grading_server_scheduler
fi

docker run -d -t -p 4000:80 --name app  grading_server_app

docker network connect grading_network app
docker network connect grading_network scheduler
