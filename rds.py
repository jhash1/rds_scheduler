import sys
import boto3
from datetime import date, timedelta
import json
import logging
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

rds_client = boto3.client('rds')
cloudwatch_client= boto3.client('cloudwatch')
ce_client = boto3.client('ce')
ssm_client = boto3.client('ssm', region_name="us-east-1")

current_date = date.today().isoformat()   
days_before = (date.today()-timedelta(days=30)).isoformat()



def Retrieve_Rds_Instances(rds_client): 
    rds_response = rds_client.describe_db_instances()
    db_instances = rds_response['DBInstances']
    db_instance_identifiers = [instance['DBInstanceIdentifier'] for instance in db_instances]
    return db_instance_identifiers
           

def returnMaxRDSConnectionsFromCloudwatchData(cloudwatch_client):
    listofdbinstances = Retrieve_Rds_Instances()
    rdsdbnamewithconnectioncount = []  
    for dbinstancename in listofdbinstances:
        cw_response = cloudwatch_client.get_metric_statistics(
            Namespace='AWS/RDS',
            MetricName='DatabaseConnections',
            StartTime=days_before,
            EndTime=date.now().timestamp(),
            Period=3600,
            Statistics=['Maximum'],
            Dimensions=[
                {
                    'Name': 'DBInstanceIdentifier',
                    'Value': dbinstancename 
                },
            ]
        )   
        
        for datapoint in cw_response['Datapoints']:
            max_connection_count = datapoint['Maximum']

            
        rdsdbnamewithconnectioncount.append((dbinstancename, max_connection_count))
    
    return rdsdbnamewithconnectioncount

def returnMonthlyRDSCostfromCostExplorer(ce_client):
    ce_response = ce_client.get_cost_and_usage(
        TimePeriod={
            'Start': days_before,
            'End': current_date
        },
        Granularity='MONTHLY',
        Metrics=['UNBLENDED_COST'],
        GroupBy=[
            {
                'Type': 'DIMENSION',
                'Key': 'SERVICE'
            },
            {
                'Type': 'TAG',
                'Key': 'env'
            }

        ]
    )
    result = ce_response['ResultsByTime'][0]
    rds_groups = []
    for group in result['Groups']:
        if 'Amazon Relational Database Service' in group['Keys']:
            metrics = group['Metrics']
            amount = metrics['UnblendedCost']['Amount']
    return amount

def PrintRDSInstances():
    RDS_Instances = []
    RDS_Instances = returnMaxRDSConnectionsFromCloudwatchData()
    rds_cost = returnMonthlyRDSCostfromCostExplorer()
    if not isinstance(RDS_Instances, list):
        print("Error: Expected a list of tuples from returnMaxRDSConnectionsFromCloudwatchData()")
        return  

    for name, count in RDS_Instances:
        result = ""
    for name, count in RDS_Instances:
        result += f"The RDS Instance Name is {name} and the connection count maximum is {count}.\n"
    return result

def getSlackParametersSSM(key, ssm_client):
    response = ssm_client.get_parameter(Name=key, WithDecryption=True)
    return response['Parameter']['Value']

keybot = "slackbottoken"
keyapp = "slackapptoken"

app = App(token=getSlackParametersSSM(keybot, ssm_client), name="AWS")

logger = logging.getLogger(__name__)

@app.message(re.compile("^rds$"))
def sendRDSInstanceList(message, say):
    channel_type = message["channel_type"]
    if channel_type != "im":
        return
    
    dm_channel = message["channel"]
    user_id = message["user"]

    logger.info(f"Sent aws to user {user_id}")

    say(text=PrintRDSInstances(), channel=dm_channel)



@app.message(re.compile("(can you|rds) shutdown"))
def rds_shutdown_slack(message, say):

    rds_cost = returnMonthlyRDSCostfromCostExplorer()
    say(
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"Would you like to terminate these RDS instances, this action will save you ${rds_cost}"},
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Click to Approve and Stop These Instances"},
                    "action_id": "button_click"
                }
            }
        ],
    )

def stopRDSInstances(instancenames, rds_client):
    for instancename in instancenames:
        rds_client.stop_db_instance(DBInstanceIdentifier=instancename)


@app.action("button_click")
def action_button_click(body, ack, say):
    # Acknowledge the action
    ack()
    say(f"<@{body['user']['id']}> approved this action")


def main():
    print(current_date)
    print(days_before)
    handler = SocketModeHandler(app, getSlackParametersSSM(keyapp, ssm_client))
    handler.start()
    


if __name__ == "__main__":
    main()



