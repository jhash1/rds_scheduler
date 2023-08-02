RDS Scheduler

Title: RDS_Scheduler is a program written in Python designed to optimize the usage and cost of Amazon Web Services (AWS) Relational Database Service (RDS) during off-peak hours. RDS is a Platform-as-a-Service (PaaS) database resource offered by AWS, billed at an hourly level. However, companies using RDS often incur expensive charges during periods of low usage. The RDS scheduler is used in conjuction with Slack to trigger a shutdown of selected instances.

Prerequisites
Before using RDS Scheduler, ensure that you have the following:
Python installed on your local machine.
The Python Boto3 library installed using 'pip install boto3'
AWS CLI configured with the necessary access credentials 
-https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html'
Slack workspace with appropriate permissions and a designated channel for RDS Scheduler's notifications.


Description:
RDS Scheduler operates as a local Python script and uses your AWS credentials for access.

RDS scheduler leverages the Python Boto3 SDK for connectivity to AWS.
AWS Access is managed through a local AWS profile locally stored in .aws/credentials file. 
Slack tokens(https://api.slack.com/authentication/token-types) will be stored in AWS Systems Manager parameter store.

RDS Connections:
RDS Connection count is retrieved from AWS Cloudwatch using the get_metric_statistics api call. RDS connection metrics are
Costs are retrieved using Cost explorer.

Slack integration is using the Bolt SDK for Python

RDS Scheduler will send results to slack and will listen for certain keywords.

Slack Integration and Commands:

‘RDS’ will sent a list of instances with a low connection count to slack using this command

Sample output:
The RDS Instance Name is database123 and the connection count maximum is 3.0.
The RDS Instance Name is database456 and the connection count maximum is 0.0.


RDS Shutdown command:


