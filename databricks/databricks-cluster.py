import sys
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json

# Capture the env
INSTANCE_ID = sys.argv[1]

# All arguments, this can be expanded as needed
CLUSTER_NAME = sys.argv[2]
SPARK_VERSION = sys.argv[3]
NODE_TYPE = sys.argv[4]
AUTOTERMINATION_MINUTES = sys.argv[5]
NUM_WORKERS = sys.argv[6]


API_VERSION = '/api/2.0'

cluster_info = {
  "cluster_name": CLUSTER_NAME,
  "spark_version": SPARK_VERSION,
  "node_type_id": NODE_TYPE,
  "autotermination_minutes": AUTOTERMINATION_MINUTES,
  "spark_conf": {
    "spark.databricks.cluster.profile" : "singleNode",
    "spark.redaction.regex" : "(?i)secret|password|token|database_url",
    "spark.master" : "local[*, 4]",
    "spark.logConf" : "true",
    "spark.databricks.service.server.enabled" : "true"
  },
  "aws_attributes": {
    "first_on_demand" : 1,
    "availability" : "SPOT_WITH_FALLBACK",
    "zone_id" : "us-gov-west-1a",
    "instance_profile_arn" : INSTANCE_PROFILE,
    "spot_bid_price_percent" : 100,
    "ebs_volume_type" : "GENERAL_PURPOSE_SSD",
    "ebs_volume_count" : 3,
    "ebs_volume_size" : 100
  },
  "num_workers": NUM_WORKERS
}


def createCluster(api_command, params):
    url = "https://{}{}{}".format(INSTANCE_ID, API_VERSION, api_command)
    response = requests.post(
      url = url,
      json = params,
    )
    return response

    
try:
    cluster_id = createCluster("/clusters/create", cluster_info)
except Exception as e:
    print(str(e))
