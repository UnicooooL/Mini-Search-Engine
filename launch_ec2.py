import boto3
import os
import time

AWS_ACCESS_KEY_ID = 'xxxxxxxxxx'
AWS_SECRET_ACCESS_KEY = 'xxxxxxxxxx'
REGION_NAME = 'us-east-1' 
GROUP_NUMBER = '1'
KEY_NAME = f'ece326-key-{GROUP_NUMBER}'
SG_NAME = f'ece326-group{GROUP_NUMBER}'
AMI_ID = 'ami-0bbdd8c17ed981ef9'
INSTANCE_TYPE = 't3.micro' 
KEY_PAIR_FILENAME = f'{KEY_NAME}.pem'

ec2_connection = boto3.client( #initializing boto client
    'ec2',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION_NAME
)
ec2_resource = boto3.resource( #initializing boto request 
    'ec2',
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=REGION_NAME
)
def create_key_pair():
    try:
        kp = ec2_connection.create_key_pair(KeyName=KEY_NAME)

        with open(KEY_PAIR_FILENAME, 'w') as f:
            f.write(kp['KeyMaterial'])
        
        os.chmod(KEY_PAIR_FILENAME, 0o400)
        return KEY_NAME
    except Exception as e: #handling exceptions 
        if 'already exists' in str(e):
            print(f"Key pair is already there.")
            return KEY_NAME
        raise e

def create_security_group(): #creating security group 
    try:
        response = ec2_connection.create_security_group(
            GroupName=SG_NAME,
            Description='ECE326 Lab 2 Security Group'
        )
        group_id = response['GroupId']

        ip_permissions = [
            {'IpProtocol': 'icmp', 'FromPort': -1, 'ToPort': -1, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
            {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]},
        ] #ip permissions according to the lab 

        ec2_connection.authorize_security_group_ingress(
            GroupId=group_id,
            IpPermissions=ip_permissions
        )
        return group_id #returning the security group id 
    
    except Exception as err: #handling exceptions
        if "Duplicate" in str(err):
            print(f"Security Group is already there.")
            details = ec2_connection.describe_security_groups(GroupNames=[SG_NAME])
            return details['SecurityGroups'][0]['GroupId']
        else:
            print("Error:",err)
            raise

    
def create_instance(): #creating a new instance 
    global kn, group_id 
    key_name = kn
    sg_id = group_id
    instances = ec2_resource.create_instances(
        MinCount=1,
        MaxCount=1,
        ImageId=AMI_ID,
        SecurityGroupIds=[sg_id],
        InstanceType=INSTANCE_TYPE,
        KeyName=key_name,
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Name', 'Value': f'ECE326-Lab2-Group{GROUP_NUMBER}'}]
            },
        ]
    )
    instance = instances[0]

    instance.wait_until_running()
    instance.reload() 

    print(f"Instance state is now: {instance.state['Name']}")
    print(f"Public IP Address: {instance.public_ip_address}")

if __name__ == "__main__":
    try:
        kn = create_key_pair()
        group_id = create_security_group()
        create_instance()
        
    except Exception as e:
        print(f"\nError: {e}")