if [[ "$(docker images -q grading_server_checker 2> /dev/null)" == "" ]]; then
  docker build checker -t grading_server_checker
fi

if [[ "$(docker images -q grading_server_app 2> /dev/null)" == "" ]]; then
  docker build app -t grading_server_app
fi

if [[ "$(docker images -q grading_server_scheduler 2> /dev/null)" == "" ]]; then
  docker build scheduler -t grading_server_scheduler
fi

if [[ "$(docker container ls -aqf grading_server_scheduler 2> /dev/null)" == "" ]]; then
  docker run -d -t -v /var/run/docker.sock:/var/run/docker.sock -p 5000:5000 grading_server_scheduler
fi

docker run -d -t -p 4000:80 grading_server_app
