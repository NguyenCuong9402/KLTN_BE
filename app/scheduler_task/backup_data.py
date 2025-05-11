from app.extensions import db, CONFIG
from app.utils import get_datetime_now
from threading import Thread
import os

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
        backup_folder_name = f"backup_{str(get_datetime_now().date())}.zip"
        image_path = './app/files/backup'
        os.system(f"zip -r {backup_folder_name} {backup_dbsql_name} {backup_mongodb_name} {image_path}")
        # upload backup to s3


        # Remove file created quá 3 ngày trong image_path
        os.system(f"find {image_path} -type f -mtime +3 -exec rm {{}} \;")

        # remove backup local in docker
        # os.system(f"rm -rf {backup_mongodb_name}")
        # os.system(f"rm {backup_dbsql_name}")
        # os.system(f"rm {backup_folder_name}")


def backup_data():
    # create two new threads
    t_backup = Thread(target=__thread_backup)
    # start the threads
    t_backup.start()
    return True
