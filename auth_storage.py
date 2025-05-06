import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth
from google.cloud import storage
import json
import os
from datetime import datetime
import glob
import pandas as pd

# Initialize Firebase Admin
def initialize_firebase():
    if not firebase_admin._apps:
        firebase_credentials = {
            "type": st.secrets["firebase"]["type"],
            "project_id": st.secrets["firebase"]["project_id"],
            "private_key_id": st.secrets["firebase"]["private_key_id"],
            "private_key": st.secrets["firebase"]["private_key"],
            "client_email": st.secrets["firebase"]["client_email"],
            "client_id": st.secrets["firebase"]["client_id"],
            "auth_uri": st.secrets["firebase"]["auth_uri"],
            "token_uri": st.secrets["firebase"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"]
        }
        cred = credentials.Certificate(firebase_credentials)
        firebase_admin.initialize_app(cred)
    return firebase_admin.get_app()

# Initialize Google Cloud Storage
def initialize_gcs():
    gcs_credentials = {
        "type": st.secrets["gcs"]["type"],
        "project_id": st.secrets["gcs"]["project_id"],
        "private_key_id": st.secrets["gcs"]["private_key_id"],
        "private_key": st.secrets["gcs"]["private_key"],
        "client_email": st.secrets["gcs"]["client_email"],
        "client_id": st.secrets["gcs"]["client_id"],
        "auth_uri": st.secrets["gcs"]["auth_uri"],
        "token_uri": st.secrets["gcs"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcs"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gcs"]["client_x509_cert_url"]
    }
    storage_client = storage.Client.from_service_account_info(gcs_credentials)
    return storage_client

# Authentication UI
def authenticate_user():
    if 'user' not in st.session_state:
        st.session_state.user = None

    if not st.session_state.user:
        st.subheader("Login or Sign Up")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Login"):
                try:
                    initialize_firebase()
                    user = auth.sign_in_with_email_and_password(email, password)  # Note: This requires Firebase client SDK
                    st.session_state.user = user
                    st.success("Logged in successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {e}")
        
        with col2:
            if st.button("Sign Up"):
                try:
                    initialize_firebase()
                    user = auth.create_user(email=email, password=password)
                    st.session_state.user = user
                    st.success("Signed up successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Sign up failed: {e}")
        return False
    return True

# GCS Operations
def save_records_to_gcs(user_uid, lecture_name, records, bucket_name):
    try:
        storage_client = initialize_gcs()
        bucket = storage_client.bucket(bucket_name)
        date = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().strftime("%H%M%S")
        file_path = f"timer_logs/{user_uid}/{lecture_name}/{date}_{timestamp}.json"
        
        blob = bucket.blob(file_path)
        blob.upload_from_string(json.dumps(records, ensure_ascii=False, indent=2), content_type='application/json')
        return file_path
    except Exception as e:
        st.error(f"Error saving to GCS: {e}")
        return None

def load_records_from_gcs(file_path, bucket_name):
    try:
        storage_client = initialize_gcs()
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_path)
        data = json.loads(blob.download_as_string())
        return data
    except Exception as e:
        st.error(f"Error loading from GCS: {e}")
        return []

def get_existing_gcs_files(user_uid, lecture_name, bucket_name):
    try:
        storage_client = initialize_gcs()
        bucket = storage_client.bucket(bucket_name)
        prefix = f"timer_logs/{user_uid}/{lecture_name}/"
        blobs = bucket.list_blobs(prefix=prefix)
        return sorted([blob.name for blob in blobs if blob.name.endswith('.json')], reverse=True)
    except Exception as e:
        st.error(f"Error listing GCS files: {e}")
        return []

def load_lecture_names_gcs(user_uid, bucket_name):
    try:
        storage_client = initialize_gcs()
        bucket = storage_client.bucket(bucket_name)
        prefix = f"timer_logs/{user_uid}/"
        blobs = bucket.list_blobs(prefix=prefix)
        lecture_names = set()
        for blob in blobs:
            parts = blob.name.split('/')
            if len(parts) > 2:
                lecture_names.add(parts[2])
        return sorted(list(lecture_names))
    except Exception as e:
        st.error(f"Error loading lecture names: {e}")
        return []