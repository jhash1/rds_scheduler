import boto3


class AwsClientGenerator:
    def __init__(self, service_name):
        self.client = boto3.client(service_name)

    def invoke_service(self, api_name, **kwargs):
        api = getattr(self.client, api_name)
        return api(**kwargs)


ec2_client = AwsClientGenerator('ec2')
response = ec2_client.invoke_service('describe_instances')
print(response)

