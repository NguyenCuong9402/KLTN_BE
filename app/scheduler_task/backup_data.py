import os
import urllib.parse
import datetime

from app.extensions import db, logger, CONFIG
from app.utils import get_datetime_now
from threading import Thread


def __thread_backup():
    with db.app.app_context():
        # export mysql
        backup_dbsql_name = f"{CONFIG.BK_DBNAME_MYSQL}_{str(get_datetime_now().date())}.sql"
        os.system(f"mysqldump -c -P {CONFIG.BK_PORT_MYSQL} -h {CONFIG.BK_HOST_MYSQL} -u {CONFIG.BK_USERNAME_MYSQL} "
                  f"--password={CONFIG.BK_PASSWORD_MYSQL} {CONFIG.BK_DBNAME_MYSQL} > {backup_dbsql_name}")
        # export mongo
        backup_mongodb_name = f"{CONFIG.MONGO_DB}_{str(get_datetime_now().date())}"
        # password_mongo = urllib.parse.unquote(CONFIG.BK_PASSWORD_MONGODB)
        uri = f"mongodb://{CONFIG.BK_USERNAME_MONGODB}:{CONFIG.BK_PASSWORD_MONGODB}@{CONFIG.BK_HOST_MONGODB}:{CONFIG.BK_PORT_MONGODB}/?authMechanism=SCRAM-SHA-256"
        os.system(f"mongodump --uri=\"{uri}\" --out={backup_mongodb_name}")

        # zip folder backup
        backup_folder_name = f"backup_fit_{str(get_datetime_now().date())}.zip"
        image_path = './app/files'
        os.system(f"zip -r {backup_folder_name} {backup_dbsql_name} {backup_mongodb_name} {image_path}")
        # upload backup to s3
        # status = upload_s3(backup_folder_name)

        # copy data backup to server another
        destination_path = "/media/bootai/Data/backup-data-fit/"
        os.system(f"sshpass -p '{CONFIG.STORAGE_PASSWORD}' scp -o StrictHostKeyChecking=no -r {backup_folder_name} "
                  f"{CONFIG.STORAGE_USER_NAME}@{CONFIG.STORAGE_SOURCE_HOST}:{destination_path}")
        # remove older backup
        two_day_before = get_datetime_now().date() - datetime.timedelta(days=2)
        file_remove = f"{destination_path}backup_fit_{str(two_day_before)}.zip"
        os.system(f"sshpass -p '{CONFIG.STORAGE_PASSWORD}' ssh {CONFIG.STORAGE_USER_NAME}@{CONFIG.STORAGE_SOURCE_HOST} rm -r {file_remove}")

        # remove backup local in docker
        os.system(f"rm -rf {backup_mongodb_name}")
        os.system(f"rm {backup_dbsql_name}")
        os.system(f"rm {backup_folder_name}")

        # if status:
        #     logger.info('{} Backup data success!!!'.format(get_datetime_now().strftime('%Y-%b-%d %H:%M:%S')))
        #     return True
        # else:
        #     logger.info('{} Backup data error!!!'.format(get_datetime_now().strftime('%Y-%b-%d %H:%M:%S')))
        #     return False


def backup_data():
    # create two new threads
    t_backup = Thread(target=__thread_backup)
    # start the threads
    t_backup.start()
    return True
