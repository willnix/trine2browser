#!/usr/bin/env python3
import sys
from random import randrange
import time

from PySide2.QtCore import Qt, Slot
from PySide2.QtWidgets import (QApplication, QGridLayout,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QWidget, QPushButton, QLineEdit, QHBoxLayout)

import Trine2Connection
    
class ServerBrowser(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        # create table
        self.table_widget = QTableWidget(0, 6)
        self.table_widget.setHorizontalHeaderLabels(["ID","Name","Level","Difficulty","Mode","Players"])
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)

        # create refresh button
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.search_public)

        # password field
        self.search_edit = QLineEdit("Password...")
        # search button
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_password)

        # search form
        self.search_form = QHBoxLayout()
        self.search_form.addWidget(self.search_edit)
        self.search_form.addWidget(self.search_button)

        # create main layout
        self.main_layout = QGridLayout()
        self.main_layout.addWidget(self.table_widget, 0, 0)
        self.main_layout.addWidget(self.refresh_button, 1, 0)
        self.main_layout.addLayout(self.search_form,2,0)
        self.setLayout(self.main_layout)

        # should connect to trine server here but the conection is pretty short lived
        # TODO: unless we continuously send heartbeats
        #self.tr2_connection = Trine2Connection.Trine2Connection()
        
        
    @Slot()
    def search_public(self):
        self.refresh_button.setEnabled(False)

        self.tr2_connection = Trine2Connection.Trine2Connection()
        games = self.tr2_connection.search_public()
        self.update(games)

        self.refresh_button.setEnabled(True)

    
    @Slot()
    def search_password(self):
        self.refresh_button.setEnabled(False)

        self.tr2_connection = Trine2Connection.Trine2Connection()
        password = self.search_edit.text()
        games = self.tr2_connection.search(password)
        self.update(games)

        self.refresh_button.setEnabled(True)


    def update(self, games):
        '''
        Populates table widget with data from a list of games
        '''
        # clean up
        self.table_widget.clearContents()
        
        # build data array
        # elements are rows
        input_data = []
        for game in games:
            # build row array
            # elements are fields
            game_line = [
                game["id"],
                game["name"],
                str(game["level"]),
                game["difficulty"],
                game["mode"],
                "%d/%d" % (game["num_players"], game["max_players"]),
            ]
            input_data.append(game_line)

        self.table_widget.setRowCount(len(input_data))
        if len(games) > 0:
            self.table_widget.setColumnCount(len(input_data[0]))
        # write data array to table
        # first iterate over rows
        for i in range(len(input_data)):
            # then over fields in row
            for j in range(len(input_data[i])):
                self.table_widget.setItem(i, j, QTableWidgetItem(input_data[i][j]))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ServerBrowser()
    w.show()
    sys.exit(app.exec_())

