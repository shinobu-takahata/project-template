import boto3
from botocore.client import Config

from app.core.config import settings


class S3Client:
    """S3クライアント（MinIO用）"""

    def __init__(self):
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            config=Config(signature_version="s3v4"),
            region_name="us-east-1",
        )
        self.bucket = settings.S3_BUCKET

    def upload_file(self, file_path: str, object_name: str) -> None:
        """ファイルアップロード"""
        self.client.upload_file(file_path, self.bucket, object_name)

    def download_file(self, object_name: str, file_path: str) -> None:
        """ファイルダウンロード"""
        self.client.download_file(self.bucket, object_name, file_path)

    def list_objects(self) -> list[str]:
        """オブジェクト一覧"""
        response = self.client.list_objects_v2(Bucket=self.bucket)
        return [obj["Key"] for obj in response.get("Contents", [])]
