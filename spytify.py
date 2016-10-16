#!/usr/bin/env python

from Crypto import Random
from Crypto.PublicKey import RSA
from datetime import datetime
from io import BytesIO
from multiprocessing import Process
from os import makedirs, path, remove
from pickle import dumps, loads
from platform import system
from pygame import error, mixer, time
from PyQt5 import QtCore, QtGui, QtWidgets
from random import choice, random
from socket import socket, AF_INET, SOCK_STREAM
from sys import argv, exit, getsizeof
from time import sleep
from uuid import getnode

from SpotipyAuthentication import Ui_AuthenticationDialog
from SpotipyInterface import Ui_Interface


class Interface(QtWidgets.QMainWindow, Ui_Interface):

    def __init__(self, username):

        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)
        self.retranslateUi(self)
        self.errortext.hide()
        self.songname.hide()
        self.playingtext.hide()
        self.animationtext.hide()

        self.count = 0
        self.volume = 1
        self.next = False
        self.random = False
        self.repeat = False
        self.pausedsong = False
        self.playingsong = None
        self.prevsong = -1
        self.currentsong = 0
        self.charlist = ['|', '/', '-', '\\']
        self.plusicon = self.tabWidget.tabIcon(1)
        self.listicon = QtGui.QIcon()
        self.listicon.addPixmap(QtGui.QPixmap(":/Playlist/Icons/Playlist.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.timer = QtCore.QTimer()
        self.animationtimer = QtCore.QTimer()
        self.usertext.setText(username)

        Communicate('getlibrary')
        self.libmusic = bytes()

        while True:
            self.libmusic += self.data

            if b'stop' in self.data:
                self.data = bytes()
                break

            self.data = server.recv(1024)

        self.libmusic = self.libmusic.decode().split('|')
        del self.libmusic[-1] # Delete end stream message

        n = 0
        m = 0

        if not self.decryption == 'stop': # Global music
            for line in self.libmusic:
                self.libinfo = self.libmusic[n].split('-')
                self.tableWidget.insertRow(n)
                self.item = QtWidgets.QTableWidgetItem(self.libinfo[0]) # Music ID
                self.tableWidget.setVerticalHeaderItem(n, self.item)
                self.tableWidget.setCurrentCell(n, 0)

                while not m == 5:
                    m += 1
                    self.item = QtWidgets.QTableWidgetItem(self.libinfo[m])
                    self.item.setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignHCenter) # Align text
                    self.tableWidget.setItem(n, m - 1, self.item)

                n += 1
                m = 0

        Communicate('getplaylist')

        if not self.decryption.encode() == b'\x00': # User playlist
            for playlist in self.decryption.split('|'): # Name of each playlist, according to it's name on the database
                self.count += 1

                self.tabWidget.setCurrentIndex(self.count)
                self.tabWidget.setTabIcon(self.tabWidget.currentIndex(), self.listicon)
                self.tabWidget.setTabText(self.tabWidget.currentIndex(), playlist.split('-')[1])

        self.count = 0
        self.tabWidget.setCurrentIndex(0)
        self.tableWidget.setCurrentCell(0, 0)
        mixer.init(44100, -16, 2, 1024*4) # Pygame sound start
        self.Select()

        self.tabWidget.currentChanged.connect(self.Playlist)
        self.tableWidget.currentItemChanged.connect(self.Select)
        self.volumelevel.valueChanged.connect(self.Volume)
        self.actionLogOut.triggered.connect(self.Exit)
        self.timer.timeout.connect(self.Playing)
        self.animationtimer.timeout.connect(self.Buffering)
        #self.tabWidget.tabCloseRequested.connect(self.Remove)

        self.playbutton.clicked.connect(self.Play)
        self.pausebutton.clicked.connect(self.Pause)
        self.stopbutton.clicked.connect(self.Stop)
        self.soundbutton.clicked.connect(self.Mute)
        self.mutebutton.clicked.connect(self.Sound)
        self.previousbutton.clicked.connect(self.Previous)
        self.nextbutton.clicked.connect(self.Next)
        self.randombutton.clicked.connect(self.Random)
        self.repeatbutton.clicked.connect(self.Repeat)
        self.crossrandom.clicked.connect(self.Random)
        self.crossrepeat.clicked.connect(self.Repeat)
        self.searchbutton.clicked.connect(self.Search)


    def Playlist(self):

        if self.tabWidget.tabText(self.tabWidget.currentIndex()) == '': # Text can't be NULL
            Communicate('newplaylist ' + str(self.tabWidget.currentIndex()))
            self.tabWidget.setTabIcon(self.tabWidget.currentIndex(), self.listicon)
            self.tabWidget.setTabText(self.tabWidget.currentIndex(), self.decryption.split('-')[1])


    def Remove(self):

        print()


    def Select(self):

        self.currentsong = self.tableWidget.currentRow()

        if not self.currentsong == self.prevsong:
            artist = self.tableWidget.item(self.tableWidget.currentRow(), 0).text()
            song = self.tableWidget.item(self.tableWidget.currentRow(), 1).text()
            album = self.tableWidget.item(self.tableWidget.currentRow(), 2).text()
            temppath = path.join(path.dirname(path.realpath(argv[0])), 'temp')
            coverpath = path.join(temppath, album + '.jpg')

            if not path.exists(temppath) == True:
                makedirs(temppath)

            if self.next == False:
                self.playbutton.show()
                self.pausebutton.hide()

            elif self.next == True:
                self.next = False

            if not path.exists(coverpath) == True: # If the album cover image wasn't asked yet
                Communicate('getcover ' + str(self.tableWidget.verticalHeaderItem(self.tableWidget.currentRow()).text()))

                with open(coverpath, 'wb') as coverwrite:
                    while True:
                        if b'stop' in Interface.data:
                            coverwrite.write(Interface.data[:-4])
                            Interface.data = bytes()
                            break

                        coverwrite.write(Interface.data) # Data from previous communication
                        Interface.data = server.recv(1024)

            image = QtGui.QPixmap(coverpath) # Load image to Qt
            self.coverlabel.setPixmap(image)
            self.coverlabel.setScaledContents(True)
            self.songname.setText(artist + ' - ' + song)
            self.coverlabel.show()
            self.songname.show()

        if self.currentsong == self.playingsong and not self.pausedsong:
            self.playbutton.hide()
            self.pausebutton.show()
            self.pausedsong = False

        self.prevsong = self.currentsong


    def Search(self):

        try:
            if not self.prevtext == self.search.text(): # Search the first music
                raise AttributeError # Search the next

            self.tableWidget.setCurrentCell(self.searcheditems[0].row(), 0)
            del self.searcheditems[0]

        except (AttributeError, IndexError):
            self.searcheditems = self.tableWidget.findItems(self.search.text(), QtCore.Qt.MatchContains)
            self.prevtext = self.search.text()

            if self.searcheditems:
                for item in self.searcheditems:
                    self.tableWidget.setCurrentCell(item.row(), 0)
                    del self.searcheditems[0]
                    break


    def Play(self):

        self.currentsong = self.tableWidget.currentRow()

        if self.currentsong == self.playingsong:
            mixer.music.unpause()

        else:
            if mixer.music.get_busy():
                mixer.music.stop()
                self.timer.stop()

            self.playingtext.setText('Buffering')
            self.animationtimer.start(0)
            self.lengthbar.setValue(0)
            self.animationtext.show()
            self.playingtext.show()

            self.playbutton.setEnabled(False) # Protect data from corruption
            self.pausebutton.setEnabled(False)
            self.stopbutton.setEnabled(False)
            self.previousbutton.setEnabled(False)
            self.nextbutton.setEnabled(False)

            Communicate('play ' + str(self.tableWidget.verticalHeaderItem(self.tableWidget.currentRow()).text()))
            self.artist = self.tableWidget.item(self.tableWidget.currentRow(), 0).text()
            self.song = self.tableWidget.item(self.tableWidget.currentRow(), 1).text()
            self.playingsong = self.currentsong
            self.previoustime = datetime.today().timestamp()
            self.music = bytes()

            self.Buffering()


    def Pause(self):

        mixer.music.pause()
        self.pausedsong = True


    def Stop(self):

        try:
            mixer.music.stop()
            mixer.music.play()
            mixer.music.pause()

        except error:
            pass


    def Previous(self):

        if mixer.music.get_pos() / 1000 >= 5 or self.tableWidget.currentRow() == 0: # Rewind music if it's still in the first 5 seconds
            mixer.music.rewind()
            mixer.music.set_pos(0)

        else: # Else goes to previous song
            self.tableWidget.setCurrentCell(self.currentsong - 1, 0)
            self.Play()


    def Next(self): # Chooses the next music to play, if Repeat and/or Random are on/off

        item = []
        self.next = True

        if self.repeat == True and self.tableWidget.currentRow() == self.tableWidget.rowCount() - 1:
            self.tableWidget.setCurrentCell(0, 0)

        elif self.repeat == False and self.tableWidget.currentRow() == self.tableWidget.rowCount() - 1:
            mixer.music.stop()

        elif self.random == True:
            while not len(item) == self.tableWidget.rowCount():
                item.append(int(self.tableWidget.verticalHeaderItem(len(item)).text()) - 1)

            del item[self.currentsong]
            self.tableWidget.setCurrentCell(choice(item), 0)

        elif self.random == False:
            self.tableWidget.setCurrentCell(self.currentsong + 1, 0)

        self.Play()


    def Mute(self):

        self.volumelevel.setSliderPosition(0)
        mixer.music.set_volume(0)


    def Sound(self):

        self.volumelevel.setSliderPosition(100)
        mixer.music.set_volume(1)


    def Volume(self):

        self.volume = self.volumelevel.sliderPosition() / 10
        mixer.music.set_volume(self.volume)

        if self.volume == 0:
            self.soundbutton.hide()
            self.mutebutton.show()

        elif not self.volume == 0:
            self.mutebutton.hide()
            self.soundbutton.show()


    def Random(self):

        if self.random == False:
            self.random = True

        elif self.random == True:
            self.random = False


    def Repeat(self):

        if self.repeat == False:
            self.repeat = True

        elif self.repeat == True:
            self.repeat = False


    def Playing(self):

        if not mixer.music.get_busy():
            self.timer.stop()
            self.Next()

        self.lengthbar.setValue(round(mixer.music.get_pos() / self.songlength))


    def Buffering(self):

        if round(datetime.today().timestamp() - self.previoustime, 2) >= 0.12: # Waiting animation 
            if self.count >= 4:
                self.count = 0

            self.animationtext.setText(self.charlist[self.count])
            self.previoustime = datetime.today().timestamp()
            self.count += 1

        if b'stop' in Interface.data:
            self.music += Interface.data[:-4]
            Interface.data = bytes()
            self.songfile = BytesIO(self.music)
            self.songlength = float(self.tableWidget.item(self.tableWidget.currentRow(), 3).text().replace(':', '.')) * 60

            mixer.music.load(self.songfile)
            mixer.music.set_volume(self.volumelevel.sliderPosition() / 10)
            mixer.music.play()

            self.playingtext.setText('Streaming: ' + self.artist + ' - ' + self.song)
            self.animationtext.hide()
            self.animationtimer.stop()
            self.timer.start(200)

            self.playbutton.setEnabled(True)
            self.pausebutton.setEnabled(True)
            self.stopbutton.setEnabled(True)
            self.previousbutton.setEnabled(True)
            self.nextbutton.setEnabled(True)

        if self.animationtimer.isActive():
            self.music += Interface.data # Data from previous communication
            Interface.data = server.recv(1024)


    def Exit(self):

        Communicate('logout')
        self.Stop()
        self.timer.stop()
        self.animationtimer.stop()
        self.close()
        self.auth = Authentication()
        self.auth.show()


class Authentication(QtWidgets.QDialog, Ui_AuthenticationDialog):

    def __init__(self):

        global keys, server, serverkey

        QtWidgets.QDialog.__init__(self)
        self.setupUi(self)
        self.mail.hide()
        self.mailtext.hide()
        self.applybutton.hide()
        self.backbutton.hide()
        self.errortext.hide()
        self.successtext.hide()

        self.loginbutton.clicked.connect(self.Login)
        self.applybutton.clicked.connect(self.Register)

        try:
            keys = RSA.generate(1024, Random.new().read)
            clientkey = dumps(keys.publickey())
            address = ('192.168.1.107', 80) # Use hostname instead

            server = socket()
            server.connect(address)
            serverkey = loads(server.recv(1024))
            server.send(clientkey)

            sleep(0.1) # Prevents data corruption

            Communicate('getsession ' + str(getnode()))

            if self.decryption.split(' ')[0] == 'session':
                username = self.decryption.split(' ')[1]
                self.username.setText(username)
                self.remember.setChecked(True)

        except OSError:
            self.errortext.setText('No server connection')
            self.errortext.show()
            self.loginbutton.setEnabled(False)
            self.applybutton.setEnabled(False)


    def Login(self):

        if self.remember.isChecked() == True: # Fill iformation if Remember is checked
            clientmessage = 'login ' + self.username.text() + ' ' + self.password.text() + ' ' + str(getnode())

        else:
            clientmessage = 'login ' + self.username.text() + ' ' + self.password.text()

        Communicate(clientmessage)

        self.errortext.hide()
        self.successtext.hide()

        if self.decryption == 'success': # Proceeds to main window if password is correct
            self.close()
            self.main = Interface(self.username.text())
            self.main.show()

        elif self.decryption == 'unmatched':
            self.errortext.setText('Username and Password don\'t match')
            self.password.clear()
            self.errortext.show()

        elif self.decryption == 'error':
            self.errortext.setText('Invalid characteres')
            self.password.clear()
            self.errortext.show()


    def Register(self):

        clientmessage = 'register ' + self.username.text() + ' ' + self.password.text() + ' ' + self.mail.text()
        Communicate(clientmessage)

        self.errortext.hide()
        self.successtext.hide()

        if self.decryption == 'registered':
            self.successtext.setText('Registration success')
            self.successtext.show()

        elif self.decryption == 'error':
            self.errortext.setText('Invalid characteres')
            self.errortext.show()

        elif self.decryption == 'sqlerror':
            self.errortext.setText('Username already in use')
            self.errortext.show()

        elif self.decryption =='usertoolong':
            self.errortext.setText('User can\'t have more than 12 characters')
            self.errortext.show()

        self.password.clear()
        self.username.clear()
        self.mail.clear()


def Communicate(clientmessage):

    encryption = serverkey.encrypt(clientmessage.encode(encoding='UTF-8'), 1024)
    server.send(encryption[0])

    servermessage = server.recv(1024)

    try:
        Authentication.decryption = keys.decrypt(servermessage).decode()
        Interface.decryption = keys.decrypt(servermessage).decode()

    except ValueError:
        Interface.data = servermessage


if __name__ == '__main__':
    app = QtWidgets.QApplication(argv)
    dialog = Authentication()
    dialog.show()
    exit(app.exec_())