import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from fastapi import HTTPException, UploadFile
from typing import Optional, Dict, Any, List
import os
from datetime import datetime
import uuid

class S3Config:
    """AWS S3 configuration and client setup"""
    
    def __init__(self):
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.bucket_name = os.getenv("S3_BUCKET_NAME", "ai-mock-interview-resumes")
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.aws_region
        )
    
    def get_bucket_url(self) -> str:
        """Get the S3 bucket URL"""
        return f"https://{self.bucket_name}.s3.{self.aws_region}.amazonaws.com"

# Global S3 configuration instance
s3_config = S3Config()


class S3Service:
    """S3 service for file operations"""
    
    def __init__(self, s3_config: S3Config):
        self.s3_client = s3_config.s3_client
        self.bucket_name = s3_config.bucket_name
        self.bucket_url = s3_config.get_bucket_url()
    
    async def upload_file(
        self, 
        file: UploadFile, 
        folder: str = "resumes",
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Upload a file to S3"""
        try:
            # Generate unique filename
            file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
            unique_filename = f"{uuid.uuid4()}.{file_extension}"
            
            # Create S3 key (path)
            if user_id:
                s3_key = f"{folder}/user_{user_id}/{unique_filename}"
            else:
                s3_key = f"{folder}/{unique_filename}"
            
            # Upload file to S3
            file_content = await file.read()
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=file.content_type or 'application/octet-stream',
                Metadata={
                    'original_filename': file.filename,
                    'uploaded_at': datetime.utcnow().isoformat(),
                    'user_id': str(user_id) if user_id else 'anonymous'
                }
            )
            
            # Generate presigned URL for access
            file_url = self.generate_presigned_url(s3_key)
            
            return {
                "success": True,
                "file_url": file_url,
                "s3_key": s3_key,
                "bucket": self.bucket_name,
                "original_filename": file.filename,
                "file_size": len(file_content),
                "content_type": file.content_type
            }
            
        except NoCredentialsError:
            raise HTTPException(
                status_code=500,
                detail="AWS credentials not configured"
            )
        except ClientError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload file: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Upload error: {str(e)}"
            )
    
    def generate_presigned_url(
        self, 
        s3_key: str, 
        expiration: int = 3600
    ) -> str:
        """Generate a presigned URL for file access"""
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return response
        except ClientError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate presigned URL: {str(e)}"
            )
    
    async def delete_file(self, s3_key: str) -> bool:
        """Delete a file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError as e:
            print(f"Failed to delete file {s3_key}: {str(e)}")
            return False
    
    async def get_file_metadata(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """Get file metadata from S3"""
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return {
                "content_type": response.get('ContentType'),
                "content_length": response.get('ContentLength'),
                "last_modified": response.get('LastModified'),
                "metadata": response.get('Metadata', {})
            }
        except ClientError:
            return None
    
    def list_user_files(self, user_id: int, folder: str = "resumes") -> List[Dict[str, Any]]:
        """List files for a specific user"""
        try:
            prefix = f"{folder}/user_{user_id}/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    "s3_key": obj['Key'],
                    "file_size": obj['Size'],
                    "last_modified": obj['LastModified'],
                    "file_url": self.generate_presigned_url(obj['Key'])
                })
            
            return files
        except ClientError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list files: {str(e)}"
            )

# Global S3 service instance
s3_service = S3Service(s3_config)
