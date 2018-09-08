import sys
import os
import re
import subprocess
# import shutil
import tarfile
import datetime
import time
import traceback

# try:
#     import pysftp
# except:
#     print()
#     print("pytsftp , module Not Found")
#     print("Install: pip3 install pysftp")
#     sys.exit(1)

########################################
# Remote sftp server Connection Details.
########################################

# Bypassed this functionallity for the Unlimited Server
# SFTP_HOST = '192.168.1.5'
# SFTP_USER = 'backupuser'
# SFTP_PASSWD = 'clado123'
# SFTP_DIR = '/home/backupuser/'
# SFTP_PORT = '22'

##############################################################
# Temp location to store local sql.dump and wordpress archive.
##############################################################

BACKUP_DIRECTORY = ''  # '/tmp/wpbackup'
BACKUP_BASE_PATH = '/kunden/homepages/'


def parsing_wpconfig(install_location):
    """
    - This function takes wordpress installation directory as argument.
    - Parse wp-config.php and retrieve all database information for backup.
    - return {'database':database,'user':user, 'password':password, 'host':host}
    """
    print('{:<5}{:30}{:^2}'.format('LOG: ', 'Parsing wp-config.php File', ':'), end='')
    config_path = 'no path found'

    try:
        config_path = os.path.normpath(install_location + '/wp-config.php')
        with open(config_path, encoding='utf-8') as fh:
            content = fh.read()
        regex_db = r'define\(\s*?\'DB_NAME\'\s*?,\s*?\'(?P<DB>.*?)\'\s*?\);'
        regex_user = r'define\(\s*?\'DB_USER\'\s*?,\s*?\'(?P<USER>.*?)\'\s*?\);'
        regex_pass = r'define\(\s*?\'DB_PASSWORD\'\s*?,\s*?\'(?P<PASSWORD>.*?)\'\s*?\);'
        regex_host = r'define\(\s*?\'DB_HOST\'\s*?,\s*?\'(?P<HOST>.*?)\'\s*?\);'
        database = re.search(regex_db, content).group('DB')
        user = re.search(regex_user, content).group('USER')
        password = re.search(regex_pass, content).group('PASSWORD')
        host = re.search(regex_host, content).group('HOST')
        print('Completed')
        return {'database': database,
                'user': user,
                'password': password,
                'host': host
                }

    except FileNotFoundError:
        print('Failed')
        print('File Not Found,', config_path)
        sys.exit(1)

    except PermissionError:
        print('Failed')
        print('Unable To read Permission Denied,', config_path)
        sys.exit(1)

    except AttributeError as err:
        print('Failed')
        print('Parsing Error wp-config.php seems to be corrupt,')
        traceback.print_tb(err.__traceback__)
        sys.exit(1)

    except UnicodeEncodeError as err:
        print('Failed')
        print('Parsing Error, there is something wrong with the formatting of wp-config.php')
        traceback.print_tb(err.__traceback__)
        sys.exit(1)

    except Exception as err:
        print('Failed')
        print('Unknown Error')
        traceback.print_tb(err.__traceback__)
        sys.exit(1)


def take_sqldump(db_details):
    """
    - This function takes parsing_wpconfig as argument.
    - Create database backup using db_details dictionary.
    """
    print('{:<5}{:30}{:^2}'.format('LOG: ', 'Creating DataBase Dump', ':'), end='')
    cmd = 'command not yet created.'

    try:
        USER = db_details['user']
        PASSWORD = db_details['password']
        HOST = db_details['host']
        DATABASE = db_details['database']
        DUMPNAME = os.path.normpath(os.path.join(BACKUP_DIRECTORY, db_details['database'] + '.sql'))
        cmd = "mysqldump  -u {} -p'{}' -h {} {}  > {}".format(
            USER, PASSWORD, HOST, DATABASE, DUMPNAME).encode(encoding="utf8")
        # print('Dump CMD: ', cmd)
        subprocess.check_output(cmd, shell=True)
        print('Completed')
        return DUMPNAME

    except subprocess.CalledProcessError:
        print('Failed')
        print(': MysqlDump Failed.')
        print('Dump CMD: ', cmd)
        # sys.exit(1)

    except UnicodeEncodeError as err:
        print('Failed')
        print('Most likely the username/password has a non-ascii character.')
        traceback.print_tb(err.__traceback__)
        print('Dump CMD: ', cmd)

    except Exception as err:
        print('Failed')
        print(': Unknown Error Occurred.')
        print('Dump CMD: ', cmd)
        traceback.print_tb(err.__traceback__)
        # sys.exit(1)


def make_archive(wordpress_path, dumpfile_path):
    """
    - This function takes wordpress install path & sqlfile dump path as args.
    - create an gzip arive under BACKUP_DIRECTORY.
    """
    print('{:<5}{:30}{:^2}'.format('LOG: ', 'Archiving WordPress & SqlDump', ':'), end='')
    archive_name = 'archive path not yet created'
    try:

        time_tag = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        dir_name = os.path.basename(wordpress_path.rstrip('/'))
        archive_name = os.path.normpath(BACKUP_DIRECTORY + '/' + dir_name + '-' + time_tag + '.tar.gz')

        with tarfile.open(archive_name, "w:gz") as tar:
            tar.add(wordpress_path)
            if dumpfile_path:
                tar.add(dumpfile_path, arcname="sql.dump")
            else:
                print('sql.dump not included in archive. Most likely due to an error in the dump.')
        print('Completed')
        return archive_name

    except FileNotFoundError:
        print('Failed')
        print(': File Not Found,', archive_name)
        sys.exit(1)

    except PermissionError:
        print('Failed')
        print(': PermissionError Denied While Copying.')
        sys.exit(1)

    except Exception as err:
        print('Failed')
        print(': Unknown error occurred while taring directory :', wordpress_path)
        traceback.print_tb(err.__traceback__)
        sys.exit(1)


# def sftp_upload(archive_path):
#     """
#     - Upload archive to sftp server.
#     """
#     print('{:<5}{:30}{:^2}'.format('LOG: ', 'Uploading Files To SFTP', ':'), end='')
#     try:
#         cnopts = pysftp.CnOpts()
#         cnopts.hostkeys = None
#         with pysftp.Connection(SFTP_HOST, username=SFTP_USER, password=SFTP_PASSWD, port=int(SFTP_PORT),
#                                cnopts=cnopts) as sftp:
#             if not sftp.exists(SFTP_DIR):
#                 sftp.makedirs(SFTP_DIR)
#             sftp.cwd(SFTP_DIR)
#             sftp.put(archive_path)
#             sftp.close()
#         print('Completed')
#
#     except AuthenticationException:
#         print('Failed')
#         print(': Sftp Authentication Failure.')
#         sys.exit(1)
#
#     except PermissionError:
#         print('Failed')
#         print(': Permission Denied Error From Server.')
#         sys.exit(1)
#     except:
#         print('Failed')
#         print(': Unknown Error Occurred.')
#         sys.exit(1)


# def remove_backupdir():
#     """
#     -  remove BACKUP_DIRECTORY which holds sql sump and archive files.
#     """
#     if os.path.exists(BACKUP_DIRECTORY):
#         shutil.rmtree(BACKUP_DIRECTORY)


def make_backupdir(location):
    """
    - Creating BACKUP_DIRECTORY which holds sql sump and archive files.
    """
    if not os.path.exists(location):
        os.makedirs(location)


def remove_old_archives_older_than(days=14):
    """
    - Removing old archives in the backup dir.
    """
    print('{:<5}{:30}{:^2}'.format('LOG: ', 'Removing old Archives', ':'), end='')
    try:
        now = time.time()
        files_removed = False
        for file in os.listdir(BACKUP_DIRECTORY):
            file_location = os.path.join(BACKUP_DIRECTORY, file)
            if os.stat(file_location).st_mtime < now - days * 86400 and os.path.isfile(file_location):
                os.remove(file_location)
                print(file + ' was removed')
                files_removed = True
        if files_removed == False:
            print('No files were removed')

    except Exception as err:
        print('Failed')
        print(': Unknown error occurred.')
        traceback.print_tb(err.__traceback__)
        sys.exit(1)


def main():
    arguments = sys.argv[1:]
    if arguments:

        if os.path.exists(BACKUP_BASE_PATH):

            for location in arguments:

                install_dir = os.path.normpath(location)
                if os.path.exists(install_dir):

                    wp_dir = os.path.basename(install_dir)
                    print('')
                    print('{:<5}{:30}{:^2}'.format('LOG: ', 'Current date & time', ':'), end='')
                    print(datetime.datetime.now().strftime('%Y-%m-%d   %H:%M:%S'))

                    print('{:<5}{:30}{:^2}'.format('LOG: ', 'Backing up directory of', ':'), end='')
                    print(install_dir)

                    global BACKUP_DIRECTORY
                    BACKUP_DIRECTORY = BACKUP_BASE_PATH + wp_dir
                    print('{:<5}{:30}{:^2}'.format('LOG: ', 'Backing up to', ':'), end='')
                    print(BACKUP_DIRECTORY)

                    make_backupdir(BACKUP_DIRECTORY)
                    database_info = parsing_wpconfig(install_dir)
                    dump_location = take_sqldump(database_info)
                    archive_path = make_archive(install_dir, dump_location)
                    # sftp_upload(archive_path)
                    remove_old_archives_older_than(14)

                else:
                    print('')
                    print('Error: Path Not Found', install_dir)
                    print('')

                # remove_backupdir()
        else:
            print('')
            print('Error: Backup Base Path not found', BACKUP_BASE_PATH)
            print('')
    else:
        print('')
        print("Description: Python script to backup wordpress website into remote server.")
        print('')
        print("This Script will backup wordpress and database information")
        print("and upload them into a remote sftp server.")
        print('')
        print('USAGE: ./wpbackup.py install_path')
        print('install_path: should be full path with ending "/"')
        print('')


if __name__ == '__main__':
    main()
