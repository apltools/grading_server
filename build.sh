if [[ "$(docker images -q grading_server_checker 2> /dev/null)" == "" ]]; then
  docker build checker -t grading_server_checker
fi

if [[ "$(docker images -q grading_server_app 2> /dev/null)" == "" ]]; then
  docker build app -t grading_server_app
fi

if [[ "$(docker images -q grading_server_scheduler 2> /dev/null)" == "" ]]; then
  docker build scheduler -t grading_server_scheduler
fi
