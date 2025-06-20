import os
import json
import base64
import boto3
import hashlib
import datetime
import subprocess


def main():
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
    run_id = os.environ['RUN_ID']
    plan_path = os.environ.get('TERRAFORM_PLAN_PATH', 'plan.tfplan')
    with open(plan_path, 'rb') as f:
        terraform_hash = hashlib.sha256(f.read()).hexdigest()
    image_digest = os.environ.get('IMAGE_DIGEST', '')
    timestamp = datetime.datetime.utcnow().isoformat() + 'Z'

    evidence = {
        'timestamp': timestamp,
        'commit': commit,
        'run_id': run_id,
        'terraform_hash': terraform_hash,
        'image_digest': image_digest,
    }

    evidence_json = json.dumps(evidence, sort_keys=True).encode()

    kms = boto3.client('kms')
    sign_response = kms.sign(
        KeyId=os.environ['KMS_KEY_ID'],
        Message=evidence_json,
        SigningAlgorithm='RSASSA_PKCS1_V1_5_SHA_256',
        MessageType='RAW'
    )

    signature = base64.b64encode(sign_response['Signature']).decode()

    with open('evidence.json', 'w') as f:
        json.dump(evidence, f, indent=2)
    with open('evidence.sig', 'w') as f:
        f.write(signature)

    s3 = boto3.client('s3')
    bucket = os.environ['S3_BUCKET']
    prefix = datetime.datetime.utcnow().strftime('%Y/%m/%d')
    s3.upload_file('evidence.json', bucket, f'{prefix}/{run_id}.json')
    s3.upload_file('evidence.sig', bucket, f'{prefix}/{run_id}.sig')

    topic = os.environ.get('SNS_TOPIC_ARN')
    if topic:
        sns = boto3.client('sns')
        sns.publish(TopicArn=topic, Subject='ML Pipeline Evidence', Message=f'Evidence collected for run {run_id}')


if __name__ == '__main__':
    main()
