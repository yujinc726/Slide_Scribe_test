import streamlit as st
import boto3
from botocore.exceptions import ClientError
import json

# Initialize S3 client
s3_client = boto3.client('s3')
BUCKET_NAME = 'slide-scribe-data'

def save_json_data(data, filename, user_id=None):
    """Save JSON data to S3 for logged-in users or session state for non-members"""
    if user_id:
        # Save to S3 in user-specific folder
        file_key = f"{user_id}/{filename}"
        try:
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=file_key,
                Body=json.dumps(data, indent=2).encode('utf-8')
            )
        except ClientError as e:
            st.error(f"Error saving JSON to S3: {e}")
    else:
        # Store in session_state for non-members
        if 'non_member_data' not in st.session_state:
            st.session_state.non_member_data = {}
        st.session_state.non_member_data[filename] = data

def load_json_data(filename, user_id=None):
    """Load JSON data from S3 for logged-in users or session state for non-members"""
    if user_id:
        # Load from S3
        file_key = f"{user_id}/{filename}"
        try:
            response = s3_client.get_object(Bucket=BUCKET_NAME, Key=file_key)
            return json.loads(response['Body'].read().decode('utf-8'))
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                return None
            st.error(f"Error loading JSON from S3: {e}")
            return None
    else:
        # Load from session_state for non-members
        return st.session_state.non_member_data.get(filename) if 'non_member_data' in st.session_state else None