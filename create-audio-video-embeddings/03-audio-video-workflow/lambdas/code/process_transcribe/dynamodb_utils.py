import json, decimal
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return str(obj)
        if isinstance(obj, float):
            return decimal.Decimal(str(obj))
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)



# get the whole item from table_name
from boto3.dynamodb.conditions import Key  # import boto3

def get_item(table, key_item):
    response = table.get_item(
        Key={k: Key(k).eq(v) for k, v in key_item.items()}
    )
    return response.get('Item')


def build_update_expression(to_update):
    attr_names = {}
    attr_values = {}
    update_expression_list = []
    for i, (key,val) in enumerate(to_update.items()):
        attr_names[f"#item{i}"] = key
        attr_values[f":val{i}"] = val

    for par in zip(attr_names.keys(), attr_values.keys()):
       update_expression_list.append(f"{par[0]} = {par[1]}")
    return attr_names, attr_values, f"SET {', '.join(update_expression_list)}"


def update_item(table, key, update_obj):
    
    # Then use the CustomEncoder to handle both Decimal and datetime
    encoded_obj = json.loads(json.dumps(update_obj, cls=CustomEncoder))

    attr_names, attr_values, update_expression = build_update_expression(encoded_obj)

    table_update = table.update_item(
        Key=key,
        UpdateExpression=update_expression,
        ExpressionAttributeNames=attr_names,
        ExpressionAttributeValues=attr_values,
        ReturnValues="ALL_NEW",
        ConditionExpression="attribute_exists(#pk)", # import boto3
        ExpressionAttributeNames={"#pk": list(key.keys())[0]}
    )
    return table_update.get("Attributes")
