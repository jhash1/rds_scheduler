import boto3
import sys
from datetime import date, timedelta
import json
import logging
import re
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler


class AWSRDS:
    def __init__(self, region_name="us-east-1"):
        self.client = boto3.client("rds")

    def __str__(self) -> str:
        rds_instances = []
        rds_instances = self.return_max_rds_connections_from_cloudwatch()
        rds_cost = self.return_monthly_rds_cost_costexplorer()
        if not isinstance(rds_instances, list):
            print("Error: Expected a list of tuples from return_maxrds_connections_from_cloudwatch()")
            return  

        for name, count in rds_instances:
            result = ""
        for name, count in rds_instances:
            result += f"The RDS Instance Name is {name} and the connection count maximum is {count}.\n"
        return result

    def retrieve_rds_instances(self): 
        rds_response = self.client.describe_db_instances()
        db_instances = rds_response['DBInstances']
        db_instance_identifiers = [instance['DBInstanceIdentifier'] for instance in db_instances]
        return db_instance_identifiers
    

    def return_max_rds_connections_from_cloudwatch(self,cloudwatch_client, date, timedelta):
        dbinstancelist = self.client.retrieve_rds_instances()
        rdsdbnamewithconnectioncount = []
        current_date = date.today().isoformat()   
        days_before = (date.today()-timedelta(days=30)).isoformat()  
        for dbinstancename in dbinstancelist:
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
    
    def stopRDSInstances(instancenames, self):
        for instancename in instancenames:
            self.stop_db_instance(DBInstanceIdentifier=instancename)
    
class AWSCostExplorer:
    def __init__(self, region_name="us-east-1"):
        self.client = boto3.client("ce")
        self.days_before = days_before
        self.current_date= current_date
    
    def return_monthly_rds_cost_costexplorer(ce_client):
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
    

    class SlackIntegration(re,logging):
       def __init__(self, region_name="us-east-1"):
        self.client = boto3.client("ssm", region_name=region_name)
        

        def get_slack_parameters_ssm(key, ssm_client):
            response = ssm_client.get_parameter(Name=key, WithDecryption=True)
            return response['Parameter']['Value']

        #keybot = "slackbottoken"
        #keyapp = "slackapptoken"

        app = App(token=get_slack_parameters_ssm("slackbottoken", self.ssm_client), name="AWS")

        logger = logging.getLogger(__name__)

        @app.message(re.compile("^rds$"))
        def rds_slack_instance_list(message, say):
            channel_type = message["channel_type"]
            if channel_type != "im":
                return
            
            dm_channel = message["channel"]
            user_id = message["user"]

            logger.info(f"Sent aws to user {user_id}")

            say(text=AWSRDS.format_rds_to_string(), channel=dm_channel)



        @app.message(re.compile("(can you|rds) shutdown"))
        def rds_shutdown_slack(message, say):

            rds_cost = AWSRDS.return_max_rds_connections_from_cloudwatch()
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

            @app.action("button_click")
            def action_button_click(body, ack, say):
                # Acknowledge the action
                ack()
                say(f"<@{body['user']['id']}> approved this action")


            def main():
                handler = SocketModeHandler(app, get_slack_parameters_ssm("slackapptoken", self.ssm_client))
                handler.start()

            if __name__ == "__main__":
                main()

