#!/usr/bin/python3

import boto3
import json
import os

def parse():
    with open(os.environ.get('TARGET_JSON_FILE')) as fpr:
        result = json.load(fpr)

    storing = dict()
    for item in result['ResultsByTime'][0]['Groups']:
        key = item['Keys'][0]
        price = float(item['Metrics']['BlendedCost']['Amount'])
        if price < 0.001:
            continue
        quantity = float(item['Metrics']['UsageQuantity']['Amount'])
        unit = item['Metrics']['UsageQuantity']['Unit']
        values = {
            'Price': price,
            'Quantity': quantity,
            'Unit': unit
        }
        storing[key] = values
        print(F'{key:<40} {price:>8,.3f} USD ({quantity:,.8g}/{unit})')
    # print(json.dumps(storing, indent=2))

parse()
