import json
import os
import sys
from typing import Any, Optional, Dict, List, Tuple
from datetime import datetime

import boto3


class Route53Uptater:
    ACTIONS = {
        'running': 'UPSERT',
        'stopping': 'DELETE'
    }

    def __init__(self):
        self.instance_id: str
        self.ip_addr: str
        self.hosted_zone_id: str
        self.action: str
        self.host_name: str
        self.identifier: str

    def get_params_from_tags(self, tags: List[Dict[str, str]]) -> None:
        for tag in tags:
            if tag['Key'].lower() == 'hostname':
                self.host_name = tag['Value'].lower()
                domain_name = os.environ.get('DomainName', '')
                if domain_name:
                    self.host_name = F"{self.host_name}.{domain_name}."
            if tag['Key'].lower() == 'identifier':
                self.identifier = tag['Value'].lower()

    def get_record(self) -> Dict[str, Any]:
        client: boto3.client = boto3.client('route53')
        query_param: Dict[str, str] = {
            'HostedZoneId': self.hosted_zone_id,
            'StartRecordName': self.host_name,
            'StartRecordType': 'A',
            'MaxItems': '1'
        }
        if self.identifier:
            query_param['StartRecordIdentifier'] = self.identifier
        res_record_sets: Dict[str, Any] = client.list_resource_record_sets(**query_param)
        return res_record_sets['ResourceRecordSets'][0]

    def prepare(self, instance_id: str, state: str) -> None:
        ec2: boto3.resource = boto3.resource('ec2')
        instance: ec2.Instance = ec2.Instance(instance_id)
        self.instance_id = instance_id
        self.ip_addr = instance.public_ip_address
        self.hosted_zone_id = os.environ['HostedZoneId']
        self.action = self.ACTIONS[state]
        self.get_params_from_tags(instance.tags)

    def execute(self) -> Dict[str, Any]:
        res_record = self.get_record()
        res_record['ResourceRecords'][0]['Value'] = self.ip_addr
        change_batch: Dict[str, Any] = {
            'Comment': 'updated by Route53Updater',
            'Changes': [{
                'Action': self.action,
                'ResourceRecordSet': res_record
            }]
        }
        print("change_batch: " + json.dumps(change_batch, default=json_dt))

        client: boto3.client = boto3.client('route53')
        response: Dict[str, Any] = client.change_resource_record_sets(
            HostedZoneId=self.hosted_zone_id,
            ChangeBatch=change_batch
        )
        return response


def json_dt(o):
    if isinstance(o, datetime):
        return o.isoformat()

def lambda_handler(event, context) -> str:
    print('event: ' + json.dumps(event, default=json_dt))
    updater = Route53Uptater()
    updater.prepare(
        event['detail']['instance-id'],
        event['detail']['state']
    )
    result = updater.execute()
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
