import json
import os
import sys
from typing import Any, Optional, Dict, List
from datetime import datetime

import boto3


class Route53Uptater:

    def __init__(self, instance_id: str):
        self.instance_id: str = instance_id
        self.host_name: str = ''
        self.identifier: str = ''
        self.ip_addr: str = ''

    def get_params_from_instance_tags(self, tags: List[Dict[str, str]]) -> None:
        for tag in tags:
            if tag['Key'].lower() == 'hostname':
                self.host_name = tag['Value'].lower()
                domain_name = os.environ.get('DomainName', '')
                if domain_name:
                    self.host_name = F"{self.host_name}.{domain_name}."
            if tag['Key'].lower() == 'identifier':
                self.identifier = tag['Value'].lower()

    def get_record(self, name: str, identifier: str = '') -> Dict[str, Any]:
        client: boto3.client = boto3.client('route53')
        query_param = {
            'HostedZoneId': os.environ.get('HostedZoneId', ''),
            'StartRecordName': self.host_name,
            'StartRecordType': 'A',
            'MaxItems': '1'
        }
        if self.identifier:
            query_param['StartRecordIdentifier'] = self.identifier
        return client.list_resource_record_sets(**query_param)

    def prepare(self) -> None:
        ec2: boto3.resource = boto3.resource('ec2')
        instance: ec2.Instance = ec2.Instance(self.instance_id)
        self.ip_addr = instance.public_ip_address
        self.get_params_from_instance_tags(instance.tags)

    def execute(self, action: str) -> Dict[str, Any]:
        record_sets = self.get_record(self.host_name, self.identifier)
        record_set = record_sets['ResourceRecordSets'][0]
        record_set['ResourceRecords'][0]['Value'] = self.ip_addr

        change_batch = {
            'Comment': 'updated by Route53Updater',
            'Changes': [{
                'Action': action,
                'ResourceRecordSet': record_set
            }]
        }
        print("change_batch: " + json.dumps(change_batch, default=json_dt))

        client: boto3.client = boto3.client('route53')
        response = client.change_resource_record_sets(
            HostedZoneId=os.environ.get('HostedZoneId'),
            ChangeBatch=change_batch
        )
        return response


def json_dt(o):
    if isinstance(o, datetime):
        return o.isoformat()

def get_action(state: str) -> str:
    ACTIONS = {
        'running': 'UPSERT',
        'stopping': 'DELETE'
    }
    return ACTIONS['state']

def lambda_handler(event, context) -> str:
    print('event: ' + json.dumps(event, default=json_dt))

    action = get_action(event['detail']['state'])

    updater = Route53Uptater(event['detail']['instance-id'])
    updater.prepare()
    result = updater.execute(action)

    print("result: " + json.dumps(result, default=json_dt))
    return json.dumps(result, default=json_dt)


if __name__ == "__main__":
    context: Dict[str, Any] = dict()
    event: Dict[str, Any] = {
        'detail': {
            'state': sys.argv[1],
            'instance-id': sys.argv[2]
        }
    }
    lambda_handler(event, context)
