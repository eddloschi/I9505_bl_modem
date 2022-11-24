#!/usr/bin/env python
import argparse
import logging
import os
import os.path
import tarfile
import zipfile
from multiprocessing import Process

BL_FILES = (
    'aboot.mbn',
    'sbl1.mbn',
    'sbl2.mbn',
    'sbl3.mbn',
    'rpm.mbn',
    'tz.mbn'
)
GSM_MODEM_FILE = ('modem.bin',)
LTE_MODEM_FILE = ('NON-HLOS.bin',)


class BL_Modem():
    def __init__(self, zip_firmware, path):
        self.zip_firmware = zip_firmware
        self.path = path
        self.pda, self.csc = os.path.splitext(os.path.basename(self.zip_firmware))[0].split('_')[:2]
        self.tar_firmware = '%(pda)s_%(csc)s_%(pda)s_HOME.tar.md5' % {'pda': self.pda, 'csc': self.csc}

    def extract_firmware(self):
        logging.info('Extracting zip content')
        with zipfile.ZipFile(self.zip_firmware) as zipped:
            zipped.extract(self.tar_firmware, path=self.path)
        logging.info('Extracting tar.md5 content')
        with tarfile.open(os.path.join(self.path, self.tar_firmware)) as tar:
            members = [member for member in tar.getmembers() if member.name in BL_FILES + GSM_MODEM_FILE + LTE_MODEM_FILE]
            self.bl_files = [member.name for member in members if member.name in BL_FILES]
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(tar, members=members, path=self.path)

    def create_tar(self, tar_filename, files):
        logging.info('Creating %s' % tar_filename)
        with tarfile.TarFile(os.path.join(self.path, tar_filename), 'w', format=tarfile.USTAR_FORMAT) as tar:
            for filename in files:
                try:
                    tar.add(os.path.join(self.path, filename), arcname=filename)
                except Exception:
                    logging.error('ERROR: %s not added to %s' % (filename, tar_filename))

    def clean_up(self, delete_original):
        logging.info('Deleting extracted files')
        for filename in tuple(self.bl_files) + GSM_MODEM_FILE + LTE_MODEM_FILE:
            try:
                os.remove(os.path.join(self.path, filename))
            except Exception:
                logging.error('ERROR: %s not deleted' % filename)
        os.remove(os.path.join(self.path, self.tar_firmware))
        if delete_original:
            logging.info('Deleting original zip')
            os.remove(self.zip_firmware)


def parse_args():
    parser = argparse.ArgumentParser(description='Create Odin flashable tars.')
    parser.add_argument('firmware', metavar='ZIPFILE', help='zip file of the firmware')
    parser.add_argument('-o', '--output-path', default='.', help='path to store the tar files')
    parser.add_argument('-d', '--delete-original', action='store_true', help='delete the original zip after creating the tar files')
    return parser.parse_args()


def main():
    logging.basicConfig(format='%(message)s', level=logging.INFO)
    args = parse_args()
    bl_modem = BL_Modem(args.firmware, args.output_path)
    bl_modem.extract_firmware()
    bl_process = Process(target=bl_modem.create_tar, args=('BL_%s_user_low_ship_MULTI_CERT.tar' % bl_modem.pda, bl_modem.bl_files))
    gsm_modem_process = Process(target=bl_modem.create_tar, args=('%s_MODEM.tar' % bl_modem.pda, GSM_MODEM_FILE))
    lte_modem_process = Process(target=bl_modem.create_tar, args=('%s_WiFi_FIX.tar' % bl_modem.pda, LTE_MODEM_FILE))
    gsm_lte_modems_process = Process(target=bl_modem.create_tar, args=('GSM_Modem_%(pda)s_and_LTE_Modem_%(pda)s.tar' % {'pda': bl_modem.pda}, GSM_MODEM_FILE + LTE_MODEM_FILE))
    bl_process.start()
    gsm_modem_process.start()
    lte_modem_process.start()
    gsm_lte_modems_process.start()
    bl_process.join()
    gsm_modem_process.join()
    lte_modem_process.join()
    gsm_lte_modems_process.join()
    bl_modem.clean_up(args.delete_original)

if __name__ == '__main__':
    main()
