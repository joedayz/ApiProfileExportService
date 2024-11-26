if JSON=$(wget -qO- http://localhost:8080);
then
  echo "Export service OK!"
  wget --method=PUT --body-data="${JSON}" https://devtest-visuale.quadim.ai/api/status/softwarefactory/profile-export-service/node1?service_tag=DEVTEST
else
  echo "Export service DOWN!"
  JSON=$(python health_fail.py); wget --method=PUT --body-data="${JSON}"  https://devtest-visuale.quadim.ai/api/status/softwarefactory/profile-export-service/node1?service_tag=DEVTEST
fi
