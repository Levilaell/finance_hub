#!/usr/bin/env python3
"""
Automated database backup script
Creates encrypted backups and uploads to cloud storage
"""
import os
import sys
import subprocess
import logging
from datetime import datetime
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
import gzip
import shutil

# Add Django project to Python path
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

from django.conf import settings
from django.core.management import call_command
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class DatabaseBackup:
    """Database backup and upload service"""
    
    def __init__(self):
        self.backup_dir = Path('/app/backups')
        self.backup_dir.mkdir(exist_ok=True)
        
        # AWS S3 configuration
        self.s3_client = None
        if hasattr(settings, 'AWS_ACCESS_KEY_ID') and settings.AWS_ACCESS_KEY_ID:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
            )
        
        self.bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'financeub-backups')
        
    def create_database_backup(self):
        """Create PostgreSQL database backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'db_backup_{timestamp}.sql'
        backup_path = self.backup_dir / backup_filename
        
        # Database configuration from Django settings
        db_config = settings.DATABASES['default']
        
        # Create pg_dump command
        cmd = [
            'pg_dump',
            '--host', db_config['HOST'],
            '--port', str(db_config['PORT']),
            '--username', db_config['USER'],
            '--dbname', db_config['NAME'],
            '--no-password',
            '--verbose',
            '--clean',
            '--no-owner',
            '--no-privileges',
            '--file', str(backup_path)
        ]
        
        # Set password via environment variable
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['PASSWORD']
        
        try:
            logger.info(f"Creating database backup: {backup_filename}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"pg_dump failed: {result.stderr}")
            
            logger.info(f"Database backup created successfully: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create database backup: {e}")
            raise
    
    def compress_backup(self, backup_path):
        """Compress backup file with gzip"""
        compressed_path = backup_path.with_suffix('.sql.gz')
        
        try:
            logger.info(f"Compressing backup: {backup_path}")
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove original uncompressed file
            backup_path.unlink()
            
            logger.info(f"Backup compressed: {compressed_path}")
            return compressed_path
            
        except Exception as e:
            logger.error(f"Failed to compress backup: {e}")
            raise
    
    def upload_to_s3(self, backup_path):
        """Upload backup to S3"""
        if not self.s3_client:
            logger.warning("S3 client not configured, skipping upload")
            return None
        
        try:
            # Create S3 key with date prefix
            date_prefix = datetime.now().strftime('%Y/%m/%d')
            s3_key = f'database-backups/{date_prefix}/{backup_path.name}'
            
            logger.info(f"Uploading backup to S3: s3://{self.bucket_name}/{s3_key}")
            
            self.s3_client.upload_file(
                str(backup_path),
                self.bucket_name,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'STANDARD_IA'  # Infrequent Access for cost savings
                }
            )
            
            s3_url = f"s3://{self.bucket_name}/{s3_key}"
            logger.info(f"Backup uploaded successfully: {s3_url}")
            return s3_url
            
        except ClientError as e:
            logger.error(f"Failed to upload backup to S3: {e}")
            raise
    
    def cleanup_old_backups(self, keep_local=7, keep_s3=30):
        """Clean up old backup files"""
        # Clean up local backups (keep last 7 days)
        try:
            local_backups = sorted(self.backup_dir.glob('db_backup_*.sql.gz'))
            if len(local_backups) > keep_local:
                for backup in local_backups[:-keep_local]:
                    logger.info(f"Removing old local backup: {backup}")
                    backup.unlink()
        except Exception as e:
            logger.error(f"Failed to cleanup local backups: {e}")
        
        # Clean up S3 backups (keep last 30 days)
        if self.s3_client:
            try:
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix='database-backups/'
                )
                
                if 'Contents' in response:
                    objects = sorted(response['Contents'], key=lambda x: x['LastModified'])
                    if len(objects) > keep_s3:
                        for obj in objects[:-keep_s3]:
                            logger.info(f"Removing old S3 backup: {obj['Key']}")
                            self.s3_client.delete_object(
                                Bucket=self.bucket_name,
                                Key=obj['Key']
                            )
            except Exception as e:
                logger.error(f"Failed to cleanup S3 backups: {e}")
    
    def send_notification(self, success, backup_path=None, s3_url=None, error=None):
        """Send backup notification email"""
        if not hasattr(settings, 'EMAIL_HOST_USER') or not settings.EMAIL_HOST_USER:
            return
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if success:
            subject = f'✅ Database Backup Successful - {timestamp}'
            message = f"""
Database backup completed successfully.

Details:
- Backup file: {backup_path.name if backup_path else 'N/A'}
- File size: {backup_path.stat().st_size / 1024 / 1024:.2f} MB
- S3 location: {s3_url or 'Not uploaded'}
- Timestamp: {timestamp}

Your FinanceHub data is safely backed up.
            """
        else:
            subject = f'❌ Database Backup Failed - {timestamp}'
            message = f"""
Database backup failed!

Error: {error}
Timestamp: {timestamp}

Please check the backup system immediately.
            """
        
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                ['admin@yourcompany.com'],  # Update with real admin email
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send notification email: {e}")
    
    def run_backup(self):
        """Run complete backup process"""
        try:
            logger.info("Starting database backup process")
            
            # Create backup
            backup_path = self.create_database_backup()
            
            # Compress backup
            compressed_path = self.compress_backup(backup_path)
            
            # Upload to S3
            s3_url = self.upload_to_s3(compressed_path)
            
            # Cleanup old backups
            self.cleanup_old_backups()
            
            # Send success notification
            self.send_notification(True, compressed_path, s3_url)
            
            logger.info("Database backup process completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Database backup process failed: {e}")
            self.send_notification(False, error=str(e))
            return False


def main():
    """Main backup function"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    backup_service = DatabaseBackup()
    success = backup_service.run_backup()
    
    if success:
        print("Backup completed successfully")
        sys.exit(0)
    else:
        print("Backup failed")
        sys.exit(1)


if __name__ == '__main__':
    main()