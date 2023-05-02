from PyQt5 import QtWidgets, QtGui
import pathlib
import os
from PyQt5.QtCore import QDate
import shutil


def UI_init(win):
    win.progressBar_label.setVisible(True)
    win.progressBar.setVisible(True)
    win.default_user_pic_path = "GraphicUserInterface" + os.sep + "images" + os.sep + "blank-profile-picture.png"

    win.dateOfBirthdateEdit.setDisplayFormat("yyyy-MM-dd")
    win.dateOfBirthdateEdit.setDate(QDate.currentDate())
    win.dateOfBirthdateEdit.setMinimumDate(QDate(1900, 1, 1))
    win.dateOfBirthdateEdit.setMaximumDate(QDate.currentDate())

    win.set_image_button.clicked.connect(lambda: browse_User_Image(win))
    win.clear_button.clicked.connect(lambda: clear_Info(win))
    win.clear_image_button.clicked.connect(lambda: set_Default_Image(win))



class User:
    def __init__(self):
        self.name = ""
        self.dob = []
        self.gender = []
        self.address = []
        self.doctor = []
        self.remark = []
        self.photo_location = []
        self.age = []

    def renew(self, win):
        self.name = win.nameLineEdit.text()
        self.dob = win.dateOfBirthdateEdit.date()
        self.address = win.addressLineEdit.text()
        self.doctor = win.doctorLineEdit.text()
        self.remark = win.remarkTextEdit.toPlainText()
        self.photo_location = win.user_manager.current_user_pic_path

        if win.genderComboBox.currentText() == 'male':
            self.gender = 'm'
        elif win.genderComboBox.currentText() == 'female':
            self.gender = 'f'

        current_date = QDate.currentDate()
        self.age = current_date.year() - self.dob.year()
        if (self.dob.month(), self.dob.day()) > (current_date.month(), current_date.day()):
            self.age -= 1

    def reverse_renew(self, win):
        win.nameLineEdit.setText(self.name)
        win.dateOfBirthdateEdit.setDate(self.dob)
        win.addressLineEdit.setText(self.address)
        win.doctorLineEdit.setText(self.doctor)
        win.remarkTextEdit.setText(self.remark)
        win.user_manager.current_user_pic_path = self.photo_location

        if self.gender == 'm':
            win.genderComboBox.setCurrentText('male')
        elif self.gender == 'f':
            win.genderComboBox.setCurrentText('female')

        current_date = QDate.currentDate()
        self.age = current_date.year() - self.dob.year()
        if (self.dob.month(), self.dob.day()) > (current_date.month(), current_date.day()):
            self.age -= 1


class UserManager:
    def __init__(self):
        self.current_user = User()
        self.current_user_pic_path = "GraphicUserInterface" + os.sep + "images" + os.sep + "blank-profile-picture.png"
        self.save_path = None

    def makeUser(self, save_path):
        self.current_user = User()
        self.save_path = save_path

    def load_data(self, mgr, fname, win):
        self.current_user = mgr.current_user

        if os.path.exists(mgr.current_user_pic_path):
            self.current_user_pic_path = mgr.current_user_pic_path
        else:
            self.current_user_pic_path = "GraphicUserInterface" + os.sep + "images" + os.sep + "blank-profile-picture.png"

        self.save_path = fname
        self.current_user.reverse_renew(win)


def clear_Info(win):
    win.nameLineEdit.clear()
    win.dateOfBirthdateEdit.setDate(QDate.currentDate())
    win.addressLineEdit.clear()
    win.doctorLineEdit.clear()
    win.remarkTextEdit.clear()
    set_Default_Image(win)
    win.user_manager.current_user = None


def browse_User_Image(win):
    current_location = str(pathlib.Path().absolute()) + os.sep
    fname = QtWidgets.QFileDialog.getOpenFileName(win, 'Open file',
                                                  current_location, "Image files (*.jpg *.gif *.png)")
    imagePath = fname[0]

    if not imagePath == "":
        resources_folder = current_location + "Resources"
        if not os.path.exists(resources_folder):
            os.makedirs(resources_folder)

        file_name = os.path.basename(imagePath)
        new_file_path = os.path.join(resources_folder, file_name)
        
        shutil.copy(imagePath, new_file_path)
        
        win.user_manager.current_user_pic_path = new_file_path
        renew_Current_Image(win)



def set_Image(win, imagePath):
    pixmap = QtGui.QPixmap(imagePath)
    win.user_photo_label.setPixmap(pixmap)
    win.user_photo_label.resize(pixmap.width(), pixmap.height())


def set_Default_Image(win):
    win.user_manager.current_user_pic_path = win.default_user_pic_path
    renew_Current_Image(win)


def renew_Current_Image(win):
    set_Image(win, win.user_manager.current_user_pic_path)


