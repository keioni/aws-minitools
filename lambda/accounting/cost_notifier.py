import boto3
import datetime
import json
import os
import urllib.request


def notify_to_slack(cost, time_period, stat_type):
  if not os.environ.get('WEBHOOK'):
    return
  items = list()
  for k, v in sorted(cost.items()):
    if k != 'AMOUNT':
      items.append('{}: ${:,.2f}'.format(k, v))
  amount_cost = '*AMOUNT: ${:,.2f}*'.format(cost['AMOUNT'])
  sysenv = os.environ.get('SYSTEM_ENV', '')
  if stat_type == 'daily':
    msg = {
      "text": "*{} {} daily cost:*\n\n{}\n\n{}".format(
        sysenv,
        time_period['Start'].strftime('%Y/%m/%d'),
        '\n'.join(items),
        amount_cost
      )
    }
  elif stat_type == 'month_cumulative':
    dt_yesterday = time_period['End'] - datetime.timedelta(days=1)
    msg = {
      "text": "*{} monthly comulative cost ({} - {}):*\n\n{}\n\n{}".format(
        sysenv,
        time_period['Start'].strftime('%Y/%m/%d'),
        dt_yesterday.strftime('%Y/%m/%d'),
        '\n'.join(items),
        amount_cost
      )
    }
  posting_data = ("payload=" + json.dumps(msg)).encode('utf-8')
  request = urllib.request.Request(
    os.environ.get('WEBHOOK'),
    data=posting_data,
    method='POST'
    )
  with urllib.request.urlopen(request) as response:
    response_body = response.read().decode('utf-8')
  print(response_body)
  return response_body

def normalize_result(resp):
  result = dict()
  amount_cost = 0.0
  for kv in resp['ResultsByTime'][0]['Groups']:
    cost = float(kv['Metrics']['BlendedCost']['Amount'])
    amount_cost += cost
    if cost >= 0.01:
      service_name = kv['Keys'][0]
      result[service_name] = cost
  key_ec2 = 'Amazon Elastic Compute Cloud - Compute'
  result[key_ec2] = result.get(key_ec2, 0) + result.pop('EC2 - Other')
  result['AMOUNT'] = amount_cost
  return result

def get_time_period(stat_type):
  tz_jst = datetime.timezone(datetime.timedelta(hours=9))
  if stat_type == 'daily':
    dt_end = datetime.datetime.now(tz_jst)
    dt_start = dt_end - datetime.timedelta(days=1)
  elif stat_type == 'month_cumulative':
    dt_end = datetime.datetime.now(tz_jst)
    dt_start = datetime.datetime(
      dt_end.year, dt_end.month, 1, 0, 0, 0, 0
    )
  time_period = {
    'Start': dt_start,
    'End': dt_end
  }
  return time_period

def lambda_handler(event, context):
  client = boto3.client('ce', 'us-east-1')
  stat_type = os.environ.get('STAT_TYPE')
  time_period = get_time_period(stat_type)
  resp = client.get_cost_and_usage(
    TimePeriod={
      'Start': time_period['Start'].strftime('%Y-%m-%d'),
      'End': time_period['End'].strftime('%Y-%m-%d')
    },
    Granularity='MONTHLY',
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
  p = normalize_result(resp)
  notify_to_slack(p, time_period, stat_type)
  print(json.dumps(p))
  return p

if __name__ == '__main__':
  p = lambda_handler(None, None)
  for k, v in sorted(p.items()):
    v = float(v)
    if v > 0.01:
      print('{}: ${:.2f}'.format(k, v))
