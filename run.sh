if [[ "$(docker images -q grading_server_check 2> /dev/null)" == "" ]]; then
  docker build check_image -t grading_server_check
fi

if [[ "$(docker images -q grading_server 2> /dev/null)" == "" ]]; then
  docker build . -t grading_server
fi

docker run -d -t -v /var/run/docker.sock:/var/run/docker.sock -p 5000:80 grading_server
