import boto3
import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone


class AwsCostNotifier:
    FOREX_RATE_API = 'https://www.gaitameonline.com/rateaj/getrate'

    def __init__(self, sysenv = ''):
        self.stat_type = os.environ.get('STAT_TYPE')
        self.webhook = os.environ.get('WEBHOOK')
        if not sysenv:
            self.sysenv = os.environ.get('SYSTEM_ENV', '')
        self.costs = dict()
        self.time_start: datetime.datetime
        self.time_end: datetime.datetime

    def __call_ce_api(self):
        client = boto3.client('ce', 'us-east-1')
        stat_type = os.environ.get('STAT_TYPE')
        time_period = self.get_time_period(stat_type)
        resp = client.get_cost_and_usage(
            TimePeriod=time_period,
            Granularity='DAILY',
            Metrics=[
                'BlendedCost'
            ],
            GroupBy=[
                {
                'Type': 'DIMENSION',
                'Key': 'SERVICE'
                }
            ]
        )
        return resp

    def __normalize_response(self, resp):
        result = dict()
        for kv in resp['ResultsByTime'][0]['Groups']:
            service_name = kv['Keys'][0]
            cost = float(kv['Metrics']['BlendedCost']['Amount'])
            if cost > 0.0:
                result[service_name] = cost
        result['Amazon Elastic Compute Cloud - Compute'] += result.pop('EC2 - Other')
        self.costs = result

    def get_time_period(self, stat_type):
        TZ_JST = timezone(timedelta(hours=+9))
        if stat_type == 'daily':
            dt_end = datetime.now(TZ_JST)
            dt_start = dt_end - timedelta(days=1)
        elif stat_type == 'month_cumulative':
            dt_end = datetime.now(TZ_JST)
            dt_start = datetime(dt_end.year, dt_end.month, 1, 0, 0, 0, 0, TZ_JST)
        self.time_start = dt_start
        self.time_end = dt_end
        time_period = {'Start': dt_start, 'End': dt_end}
        return time_period

    def notify(self, time_period):
        if not self.webhook:
            return
        items = list()
        for k, v in sorted(self.costs.items()):
            items.append('{}: {:.2f}'.format(k, float(v)))
        if self.stat_type == 'daily':
            msg = {
                "text": "*{} {} daily cost:*\n\n{}".format(
                self.sysenv,
                time_period,
                '\n'.join(items)
                )
            }
        elif self.stat_type == 'month_cumulative':
            msg = {
                "text": "*{}: monthly comulative cost:*\n\n{}".format(
                self.sysenv,
                '\n'.join(items)
                )
            }
        posting_data = ("payload=" + json.dumps(msg)).encode('utf-8')
        request = urllib.request.Request(
            self.webhook,
            data=posting_data,
            method='POST'
        )
        with urllib.request.urlopen(request) as response:
            response_body = response.read().decode('utf-8')
        print(response_body)
        return response_body

    def get(self):
        resp = self.__call_ce_api()
        self.__normalize_response(resp)

    # def to_jpy(self, usd_price):
    #     request = urllib.request.Request(self.FOREX_RATE_API)
    #     with urllib.request.urlopen(request) as response:
    #         response_body = response.read().decode('utf-8')
