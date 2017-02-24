'''
Program written by Nicolas Merle to record MIDI interface output on disk
'''
import subprocess
import time
import os
import shutil
import RPi.GPIO as GPIO

MIDEXT= ".mid"
FOLDER= "/home/pi/Music/Emma"
BRAND= "CH345"
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
BUT1= 22
BUT2= 23
RED= 21
YELLOW= 19
GREEN= 13
GPIO.setup(BUT1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(BUT2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(GREEN, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(YELLOW, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(RED, GPIO.OUT, initial=GPIO.LOW)
GPIO.output(GREEN, GPIO.LOW)
GPIO.output(YELLOW, GPIO.LOW)
GPIO.output(RED, GPIO.LOW)
WINPATH="//192.168.0.16/Midi"
LOCALSHARE="/home/pi/windows-share"

import logging

from logging.handlers import RotatingFileHandler

logger = logging.getLogger()
# par defaut, a changer si different niveaux de logs
logger.setLevel(logging.DEBUG)
# formattage du fichier de log
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
# gere la rotation des logs
file_handler = RotatingFileHandler('/var/log/recorder.log', 'a', 1000000, 1)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def launch_record(port,output):
    ofile=output + MIDEXT
    cofile = FOLDER + "/" + ofile
    record = subprocess.Popen(['arecordmidi', '-p', port, cofile])
    time.sleep(1)
    while not GPIO.input(BUT1):
        if record.poll():
            raise EnvironmentError("The arecordmidi raised an error")
        yield  "light"
    else:
        record.terminate()

def get_port():
    devices = subprocess.check_output(['arecordmidi', '-l'])
    port = None
    lines = devices.split("\n")
    for line in lines:
        if BRAND in line:
            port = line.split(" ")[1]
    if port == None:
        raise EnvironmentError("The capture device is not connected or cannot be found")
    return port

def transfer_files(winpath, localshare, folder):
    files = os.listdir(folder)
    if len(files) == 0:
        raise ValueError("no file in the music folder")
    out = subprocess.check_output(["mount"])
    if not localshare in out:
        subprocess.check_call(['mount.cifs', "-o", "password=''", winpath, localshare])
    for mfile in files:
        sfile = folder + "/" + mfile
        dfile = localshare + "/" + mfile
        shutil.move(sfile,dfile)
    logger.info("Copy finished")
    for sec in range(0, 4):
        GPIO.output(GREEN, GPIO.HIGH)
        time.sleep(0.2)
        GPIO.output(GREEN, GPIO.LOW)
        time.sleep(0.2)
    logger.info("Umounting")
    subprocess.check_call(["umount", localshare])


def main():
    logger.info('ready')
    while True:
        time.sleep(0.05)
        if GPIO.input(BUT1) == True:
            port = get_port()
            date = time.strftime("%Y_%m_%d--%H.%M.%S", time.localtime())
            ofile = "record" + "." + date
            logger.info("starting record in " + ofile + " on port " + port)
            GPIO.output(YELLOW, GPIO.HIGH)
            for signal in launch_record(port, ofile):
                GPIO.output(YELLOW, GPIO.HIGH)
                time.sleep(0.5)
                GPIO.output(YELLOW, GPIO.LOW)
                time.sleep(0.5)
            logger.info("Record done")
            GPIO.output(GREEN, GPIO.HIGH)
            time.sleep(2)
            GPIO.output(GREEN, GPIO.LOW)
            return
        elif GPIO.input(BUT2) == True:
            transfer_files(WINPATH, LOCALSHARE, FOLDER)
            time.sleep(0.2)
            return


if __name__ == '__main__':
    logger.info("Deamon started")
    while True:
        try:
            main()
        except KeyboardInterrupt:
            exit()
        except Exception as error:
            logger.error("%s restarting",error)
            for sec in range(0,4):
                GPIO.output(RED, GPIO.HIGH)
                time.sleep(0.2)
                GPIO.output(RED, GPIO.LOW)
                time.sleep(0.2)
