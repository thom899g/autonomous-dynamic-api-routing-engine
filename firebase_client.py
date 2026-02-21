"""
Firebase client for state management and real-time data synchronization.
Handles all Firestore operations with proper error handling and connection management.
"""
import json
import os
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from contextlib import contextmanager

import firebase_admin
from firebase_admin import credentials, firestore, exceptions
from google.cloud.firestore_v1 import Client as FirestoreClient
from google.cloud.firestore_v1.document import DocumentReference
from google.cloud.firestore_v1.collection import CollectionReference

from config import config
import structlog

logger = structlog.get_logger(__name__)


class FirebaseClient:
    """Firebase Firestore client with connection management and error handling."""
    
    def __init__(self):
        """Initialize Firebase client with configuration."""
        self._app = None
        self._db: Optional[FirestoreClient] = None
        self._initialized = False
        
    def initialize(self) -> bool:
        """
        Initialize Firebase connection.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            if self._initialized and self._app:
                logger.info("Firebase already initialized")
                return True
            
            # Check for credentials file
            creds_path = config.firebase.credentials_path
            if not os.path.exists(creds_path):
                logger.error("Firebase credentials file not found", path=creds_path)
                raise FileNotFoundError(f"Firebase credentials file not found: {creds_path}")
            
            # Initialize Firebase app
            cred = credentials.Certificate(creds_path)
            
            # Initialize with project ID from config
            firebase_admin.initialize_app(cred, {
                'projectId': config.firebase.project_id,
                'databaseURL': config.firebase.database_url
            })
            
            self._app = firebase_admin.get_app()
            self._db = firestore.client()
            self._initialized = True
            
            logger.info("Firebase initialized successfully", 
                       project_id=config.firebase.project_id)
            return True
            
        except exceptions.FirebaseError as e:
            logger.error("Firebase initialization error", error=str(e), error_type=type(e).__name__)
            raise
        except Exception as e:
            logger.error("Unexpected error during Firebase initialization", 
                        error=str(e), error_type=type(e).__name__)
            raise
    
    @property
    def db(self) -> FirestoreClient:
        """Get Firestore database client."""
        if not self._initialized or not self._db:
            self.initialize()
        return self._db
    
    @contextmanager
    def transaction(self):
        """Context manager for Firestore transactions."""
        transaction = self.db.transaction()
        try:
            yield transaction
        except Exception as e:
            logger.error("Transaction failed", error=str(e))
            raise
    
    def create_document(self, collection: str, data: Dict[str, Any], 
                       document_id: Optional[str] = None) -> str:
        """
        Create a new document in Firestore.
        
        Args:
            collection: Collection name
            data: Document data
            document_id: Optional document ID (auto-generated if None)
            
        Returns:
            str: Document ID
            
        Raises:
            FirebaseError: If operation fails
        """
        try:
            if document_id:
                doc_ref = self.db.collection(collection).document(document_id)
                doc_ref.set(data)
                logger.debug("Document created with custom ID", 
                           collection=collection, document_id=document_id)
            else:
                doc_ref = self.db.collection(collection).add(data)
                document_id = doc_ref[1].id
                logger.debug("Document created with auto-generated ID", 
                           collection=collection, document_id=document_id)
            
            return document_id
            
        except exceptions.FirebaseError as e:
            logger.error("Failed to create document", 
                        collection=collection, error=str(e))
            raise
    
    def get_document(self, collection: str, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document from Firestore.
        
        Args: