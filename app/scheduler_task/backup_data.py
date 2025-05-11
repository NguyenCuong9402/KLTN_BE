from app.extensions import db, CONFIG
from app.settings import logger
from app.utils import get_datetime_now
from threading import Thread
import os

import boto3

def upload_to_s3(backup_dbsql_name):
    try:
        s3 = boto3.client(
            's3',
            endpoint_url=CONFIG.MINIO_ENDPOINT,
            aws_access_key_id=CONFIG.MINIO_ACCESS_KEY,
            aws_secret_access_key=CONFIG.MINIO_SECRET_KEY,
            region_name="us-east-1"
        )

        # Tạo bucket nếu chưa có
        existing_buckets = s3.list_buckets()
        bucket_names = [bucket['Name'] for bucket in existing_buckets['Buckets']]
        if CONFIG.MINIO_BUCKET_NAME not in bucket_names:
            s3.create_bucket(Bucket=CONFIG.MINIO_BUCKET_NAME)

        object_name = f"backup/{os.path.basename(backup_dbsql_name)}"
        s3.upload_file(backup_dbsql_name, CONFIG.MINIO_BUCKET_NAME, object_name)
        logger.info(f"Đã upload file backup lên MinIO: {object_name}")
    except Exception as e:
        logger.error(f"Lỗi khi upload S3: {str(e)}")


def __thread_backup():
    with db.app.app_context():
        # export mysql

        try:
            logger.info("Đã chạy vào backup----------------------")
            logger.info("backup mysql----------------------")

            image_path = './app/files/backup'
            os.makedirs(image_path, exist_ok=True)

            timestamp = get_datetime_now().strftime('%Y-%m-%d_%H-%M')
            backup_dbsql_name = os.path.join(image_path, f"{CONFIG.BK_DBNAME_MYSQL}_{timestamp}.sql")

            os.system(f"mysqldump -c -P {CONFIG.BK_PORT_MYSQL} -h {CONFIG.BK_HOST_MYSQL} -u {CONFIG.BK_USERNAME_MYSQL} "
                      f"--password={CONFIG.BK_PASSWORD_MYSQL} {CONFIG.BK_DBNAME_MYSQL} > {backup_dbsql_name}")

            #Upload s3
            upload_to_s3(backup_dbsql_name)

            os.system(f"find {image_path} -type f -mtime +3 -exec rm {{}} \;")
        except Exception as ex:
            logger.info(f"{str(ex)}")


def backup_data():
    # create two new threads
    t_backup = Thread(target=__thread_backup)
    # start the threads
    t_backup.start()
    return True
