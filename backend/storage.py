"""
storage.py - Audio File Storage Management

PURPOSE:
    Handle audio file uploads to Supabase Storage.
    Manages audio chunks and processed files.
"""

import os
import uuid
from typing import BinaryIO
from fastapi import UploadFile, HTTPException
from config import settings
import httpx
from datetime import datetime


class SupabaseStorage:
    """Supabase Storage client for audio files"""
    
    def __init__(self):
        self.base_url = f"{settings.SUPABASE_URL}/storage/v1"
        self.bucket = settings.STORAGE_BUCKET
        self.service_key = settings.SUPABASE_SERVICE_ROLE_KEY
        
    def _get_headers(self) -> dict:
        """Get headers for Supabase Storage API requests"""
        return {
            "Authorization": f"Bearer {self.service_key}",
            "apikey": self.service_key,
        }
    
    async def upload_chunk(
        self,
        session_id: uuid.UUID,
        chunk_number: int,
        file: UploadFile
    ) -> str:
        """
        Upload audio chunk to Supabase Storage.
        
        Args:
            session_id: Recording session ID
            chunk_number: Chunk sequence number
            file: Audio file to upload
            
        Returns:
            Storage path of uploaded file
            
        Raises:
            HTTPException: If upload fails
        """
        # Generate storage path
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_ext = os.path.splitext(file.filename)[1] if file.filename else ".m4a"
        storage_path = f"sessions/{session_id}/chunks/chunk_{chunk_number:04d}_{timestamp}{file_ext}"
        
        # Read file content
        content = await file.read()
        
        # Upload to Supabase Storage
        url = f"{self.base_url}/object/{self.bucket}/{storage_path}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    **self._get_headers(),
                    "Content-Type": file.content_type or "audio/m4a",
                },
                content=content,
                timeout=60.0
            )
            
            if response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload chunk: {response.text}"
                )
        
        return storage_path
    
    async def upload_processed_audio(
        self,
        session_id: uuid.UUID,
        file_content: bytes,
        filename: str = "processed.wav"
    ) -> str:
        """
        Upload processed audio file to Supabase Storage.
        
        Args:
            session_id: Recording session ID
            file_content: Audio file content
            filename: Output filename
            
        Returns:
            Storage path of uploaded file
        """
        storage_path = f"sessions/{session_id}/processed/{filename}"
        url = f"{self.base_url}/object/{self.bucket}/{storage_path}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    **self._get_headers(),
                    "Content-Type": "audio/wav",
                },
                content=file_content,
                timeout=120.0
            )
            
            if response.status_code not in [200, 201]:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to upload processed audio: {response.text}"
                )
        
        return storage_path
    
    def get_public_url(self, storage_path: str) -> str:
        """
        Get public URL for a stored file.
        
        Args:
            storage_path: Path in storage bucket
            
        Returns:
            Public URL to access the file
        """
        return f"{self.base_url}/object/public/{self.bucket}/{storage_path}"
    
    async def delete_file(self, storage_path: str) -> bool:
        """
        Delete file from Supabase Storage.
        
        Args:
            storage_path: Path in storage bucket
            
        Returns:
            True if successful
        """
        url = f"{self.base_url}/object/{self.bucket}/{storage_path}"
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                url,
                headers=self._get_headers(),
                timeout=30.0
            )
            
            return response.status_code in [200, 204]
    
    async def list_session_chunks(self, session_id: uuid.UUID) -> list[str]:
        """
        List all audio chunks for a session.
        
        Args:
            session_id: Recording session ID
            
        Returns:
            List of storage paths
        """
        prefix = f"sessions/{session_id}/chunks/"
        url = f"{self.base_url}/object/list/{self.bucket}"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers=self._get_headers(),
                json={"prefix": prefix},
                timeout=30.0
            )
            
            if response.status_code != 200:
                return []
            
            files = response.json()
            return [f"{prefix}{file['name']}" for file in files]


# Global storage instance
storage = SupabaseStorage()
