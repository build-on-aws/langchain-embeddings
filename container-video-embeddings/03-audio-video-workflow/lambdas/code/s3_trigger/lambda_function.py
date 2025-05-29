import boto3
import os
import json
import urllib.parse
import time
import os.path

# Inicializar clientes
sfn_client = boto3.client('stepfunctions')
s3_client = boto3.client('s3')

# Obtener variables de entorno
STATE_MACHINE_ARN = os.environ.get("STATE_MACHINE_ARN")
BUCKET_NAME = os.environ.get("BUCKET_NAME")

def lambda_handler(event, context):
    """
    Esta función se activa cuando se carga un archivo en el bucket de S3.
    Verifica si el archivo es un video y, de ser así, inicia el flujo de trabajo.
    """
    print(f"Evento recibido: {json.dumps(event)}")
    
    # Obtener información del bucket y el objeto desde el evento
    try:
        bucket = event['Records'][0]['s3']['bucket']['name']
        key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
        
        print(f"Archivo detectado: s3://{bucket}/{key}")
        
        # Verificar si el archivo es un video (por extensión)
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.wmv']
        is_video = any(key.lower().endswith(ext) for ext in video_extensions)
        
        if not is_video:
            print(f"El archivo {key} no es un video. No se iniciará el flujo de trabajo.")
            return {
                'statusCode': 200,
                'body': 'El archivo no es un video, no se procesará.'
            }
        
        # Construir el URI de S3 para el archivo
        s3_uri = f"s3://{bucket}/{key}"
        
        # Obtener el nombre del archivo sin la ruta
        filename = os.path.basename(key)
        # Tomar los primeros 6 caracteres del nombre del archivo (o menos si es más corto)
        file_prefix = filename[:6] if len(filename) >= 6 else filename
        # Obtener el timestamp actual
        timestamp = str(int(time.time()))
        # Generar el nombre de la máquina combinando timestamp y prefijo del archivo
        machine_name = f"{timestamp}-{file_prefix}"
        
        # Iniciar el flujo de trabajo de Step Functions
        response = sfn_client.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            name=f"s3-trigger-{machine_name}",
            input=json.dumps({
                's3_uri': s3_uri,
                'sftoken': machine_name
            })
        )
        
        print(f"Flujo de trabajo iniciado con ARN: {response['executionArn']}")
        
        return {
            'statusCode': 200,
            'body': f"Flujo de trabajo iniciado para el video: {key}",
            'executionArn': response['executionArn']
        }
        
    except Exception as e:
        print(f"Error al procesar el evento: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"Error al procesar el evento: {str(e)}"
        }