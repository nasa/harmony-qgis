#!/bin/bash

function cleanup {
  # remove the container
  echo "Cleaning up..."
  docker kill qgis
  docker rm qgis
}

docker run -d --name qgis -v "$PWD:/tests_directory/harmony-qgis" -e DISPLAY=:99 qgis/qgis:latest
until [ "`docker inspect -f {{.State.Running}} qgis`"=="true" ]; do
    sleep 0.1;
done
sleep 10

# copy .netrc
docker cp ~/.netrc qgis:/root

# install the harmony plugin
docker exec -it qgis sh -c "qgis_setup.sh harmony-qgis"

# run the tests
for test in  test.test_qgis_environment test.test_harmony_qgis test.test_harmony_qgis_dialog test.test_resources test.test_init
do
  docker exec -it qgis sh -c "cd /tests_directory/harmony-qgis && PYTHONPATH=/tests_directory/harmony-qgis qgis_testrunner.sh ${test}"
  if [ $? -ne 0 ]
  then 
    cleanup
    exit 255
  fi
done

cleanup
