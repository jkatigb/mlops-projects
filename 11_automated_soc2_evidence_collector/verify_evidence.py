#!/usr/bin/env python3
"""
Evidence Verification Script for Auditors

This script verifies the authenticity of collected evidence by checking
the KMS signature against the evidence JSON.
"""

import os
import sys
import json
import base64
import boto3
import argparse


def download_evidence(bucket: str, run_id: str, date: str) -> tuple:
    """Download evidence and signature files from S3."""
    s3 = boto3.client('s3')
    
    evidence_key = f"{date}/{run_id}.json"
    signature_key = f"{date}/{run_id}.sig"
    
    try:
        print(f"Downloading evidence from s3://{bucket}/{evidence_key}")
        s3.download_file(bucket, evidence_key, 'evidence.json')
        
        print(f"Downloading signature from s3://{bucket}/{signature_key}")
        s3.download_file(bucket, signature_key, 'evidence.sig')
        
        return 'evidence.json', 'evidence.sig'
    except Exception as e:
        print(f"Error downloading files: {e}")
        sys.exit(1)


def verify_signature(key_id: str, evidence_file: str, signature_file: str) -> bool:
    """Verify the evidence signature using AWS KMS."""
    kms = boto3.client('kms')
    
    # Read evidence
    with open(evidence_file, 'r') as f:
        evidence = json.load(f)
    
    # Recreate the exact signed message
    evidence_json = json.dumps(evidence, sort_keys=True).encode()
    
    # Read signature
    with open(signature_file, 'r') as f:
        signature_b64 = f.read().strip()
    signature = base64.b64decode(signature_b64)
    
    try:
        response = kms.verify(
            KeyId=key_id,
            Message=evidence_json,
            Signature=signature,
            SigningAlgorithm='RSASSA_PKCS1_V1_5_SHA_256',
            MessageType='RAW'
        )
        
        return response['SignatureValid']
    except Exception as e:
        print(f"Error verifying signature: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Verify SOC-2 evidence signatures')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--run-id', required=True, help='MLflow run ID')
    parser.add_argument('--date', required=True, help='Date in YYYY/MM/DD format')
    parser.add_argument('--key-id', required=True, help='KMS key ID or ARN')
    parser.add_argument('--local', action='store_true', help='Use local files instead of downloading')
    
    args = parser.parse_args()
    
    if args.local:
        evidence_file = 'evidence.json'
        signature_file = 'evidence.sig'
        if not os.path.exists(evidence_file) or not os.path.exists(signature_file):
            print("Error: Local evidence files not found")
            sys.exit(1)
    else:
        evidence_file, signature_file = download_evidence(args.bucket, args.run_id, args.date)
    
    # Display evidence
    with open(evidence_file, 'r') as f:
        evidence = json.load(f)
    
    print("\nEvidence Content:")
    print(json.dumps(evidence, indent=2))
    
    # Verify signature
    print("\nVerifying signature...")
    is_valid = verify_signature(args.key_id, evidence_file, signature_file)
    
    if is_valid:
        print("\n✅ SIGNATURE VALID - Evidence has not been tampered with")
        print(f"   Run ID: {evidence['run_id']}")
        print(f"   Commit: {evidence['commit']}")
        print(f"   Timestamp: {evidence['timestamp']}")
    else:
        print("\n❌ SIGNATURE INVALID - Evidence may have been tampered with!")
        sys.exit(1)


if __name__ == '__main__':
    main()