#!/usr/bin/env python3
"""
SOC-2 Evidence Collector for ML Pipelines

This script collects and signs evidence for ML pipeline runs, including:
- Git commit hash
- MLflow run ID
- Terraform plan hash
- Container image digest

The evidence is signed using AWS KMS and stored in S3 for audit purposes.
"""

import os
import sys
import json
import base64
import boto3
import hashlib
import datetime
import subprocess
from typing import Dict, Optional


def get_git_commit() -> str:
    """Get the current git commit hash."""
    try:
        return subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip()
    except subprocess.CalledProcessError as e:
        print(f"Error getting git commit: {e}")
        sys.exit(1)


def compute_file_hash(filepath: str) -> str:
    """Compute SHA256 hash of a file."""
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)
    
    sha256_hash = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def validate_environment() -> Dict[str, str]:
    """Validate required environment variables."""
    required_vars = ['RUN_ID', 'KMS_KEY_ID', 'S3_BUCKET']
    env_vars = {}
    
    for var in required_vars:
        value = os.environ.get(var)
        if not value:
            print(f"Error: Required environment variable {var} is not set")
            sys.exit(1)
        env_vars[var] = value
    
    # Optional variables
    env_vars['TERRAFORM_PLAN_PATH'] = os.environ.get('TERRAFORM_PLAN_PATH', 'plan.tfplan')
    env_vars['IMAGE_DIGEST'] = os.environ.get('IMAGE_DIGEST', '')
    env_vars['SNS_TOPIC_ARN'] = os.environ.get('SNS_TOPIC_ARN')
    
    return env_vars


def main():
    """Main evidence collection function."""
    print("Starting SOC-2 evidence collection...")
    
    # Validate environment
    env_vars = validate_environment()
    
    # Collect evidence data
    commit = get_git_commit()
    run_id = env_vars['RUN_ID']
    terraform_hash = compute_file_hash(env_vars['TERRAFORM_PLAN_PATH'])
    image_digest = env_vars['IMAGE_DIGEST']
    timestamp = datetime.datetime.utcnow().isoformat() + 'Z'
    
    evidence = {
        'timestamp': timestamp,
        'commit': commit,
        'run_id': run_id,
        'terraform_hash': terraform_hash,
        'image_digest': image_digest,
        'evidence_version': '1.0',
        'signing_algorithm': 'RSASSA_PKCS1_V1_5_SHA_256'
    }
    
    print(f"Evidence collected: {json.dumps(evidence, indent=2)}")
    
    # Prepare for signing
    evidence_json = json.dumps(evidence, sort_keys=True).encode()
    
    try:
        # Sign with KMS
        kms = boto3.client('kms')
        sign_response = kms.sign(
            KeyId=env_vars['KMS_KEY_ID'],
            Message=evidence_json,
            SigningAlgorithm='RSASSA_PKCS1_V1_5_SHA_256',
            MessageType='RAW'
        )
        signature = base64.b64encode(sign_response['Signature']).decode()
        print("Evidence signed successfully")
        
    except Exception as e:
        print(f"Error signing evidence: {e}")
        sys.exit(1)
    
    # Save locally
    with open('evidence.json', 'w') as f:
        json.dump(evidence, f, indent=2)
    with open('evidence.sig', 'w') as f:
        f.write(signature)
    
    try:
        # Upload to S3
        s3 = boto3.client('s3')
        bucket = env_vars['S3_BUCKET']
        prefix = datetime.datetime.utcnow().strftime('%Y/%m/%d')
        
        evidence_key = f'{prefix}/{run_id}.json'
        signature_key = f'{prefix}/{run_id}.sig'
        
        s3.upload_file('evidence.json', bucket, evidence_key)
        s3.upload_file('evidence.sig', bucket, signature_key)
        
        print(f"Evidence uploaded to s3://{bucket}/{evidence_key}")
        print(f"Signature uploaded to s3://{bucket}/{signature_key}")
        
    except Exception as e:
        print(f"Error uploading to S3: {e}")
        sys.exit(1)
    
    # Send notification if configured
    topic = env_vars.get('SNS_TOPIC_ARN')
    if topic:
        try:
            sns = boto3.client('sns')
            message = f"""SOC-2 Evidence Collected

Run ID: {run_id}
Commit: {commit}
Timestamp: {timestamp}
Evidence: s3://{bucket}/{evidence_key}
"""
            sns.publish(
                TopicArn=topic,
                Subject='ML Pipeline Evidence Collected',
                Message=message
            )
            print("Notification sent successfully")
        except Exception as e:
            print(f"Warning: Failed to send SNS notification: {e}")
    
    print("Evidence collection completed successfully")


if __name__ == '__main__':
    main()
