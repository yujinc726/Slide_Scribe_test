import streamlit as st
import boto3
import json

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=st.secrets.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=st.secrets.get("AWS_SECRET_ACCESS_KEY"),
    region_name=st.secrets.get("AWS_DEFAULT_REGION")
)
BUCKET_NAME = "slide-scribe-data"

def save_json_to_s3(user_id, json_data, filename):
    """Save JSON data to S3 under user_id folder with specified filename."""
    try:
        file_path = f"{user_id}/{filename}"
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=file_path,
            Body=json.dumps(json_data, ensure_ascii=False).encode('utf-8')
        )
    except Exception as e:
        st.error(f"Error saving to S3: {e}")

def load_json_from_s3(user_id, filename):
    """Load JSON data from S3 for a user with specified filename."""
    try:
        file_path = f"{user_id}/{filename}"
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=file_path)
        return json.loads(response['Body'].read().decode('utf-8'))
    except s3_client.exceptions.NoSuchKey:
        return {}
    except Exception as e:
        st.error(f"Error loading from S3: {e}")
        return {}