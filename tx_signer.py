#!/usr/bin/python3

import sys
from ethereum.transactions import Transaction
from ethereum.tools import keys
from json import load as jload
from rlp import encode as rlpencode
from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QApplication, QDialog, QFileDialog
from math import ceil


class MainWindow(QDialog):
    def __init__(self):
        super().__init__()

        # Set up the user interface from Designer.
        uic.loadUi('sign_raw_transaction.ui', self)

        # Create the event handlers
        # button handler
        self.pushbutton_generate.clicked.connect(self.generateTX)

        # Input method for networkid
        self.radiobutton_networkid_textbox.clicked.connect(self.setNetworkIDField)
        self.radiobutton_networkid_dropdown.clicked.connect(self.setNetworkIDField)

        # Input method for private key
        self.radiobutton_keystore.clicked.connect(self.setKeyField)
        self.radiobutton_key.clicked.connect(self.setKeyField)

        # Insert file dialog manually
        self.pushbutton_browse.clicked.connect(self.browse)
        self.show()

    def browse(self):
        self.textbox_keystore.setText(QFileDialog().\
            getOpenFileName(None, 'Select keystore file', '', '')[0])

    # toggle between network id input methods
    def setNetworkIDField(self):
        textbox = self.radiobutton_networkid_textbox.isChecked()
        self.combobox_networkid.setEnabled(not textbox)
        self.textbox_networkid.setEnabled(textbox)

    # toggle between private key input methods
    def setKeyField(self):
        keystore = self.radiobutton_keystore.isChecked()      
        self.textbox_keystore.setEnabled(keystore)
        self.textbox_keystore_pw.setEnabled(keystore)
        self.pushbutton_browse.setEnabled(keystore)
        self.textbox_privatekey.setEnabled(not keystore)

    # Using this function the conversion from bytes to hex does include the first zero
    def safeBytesToHex(self, bytes_value, excepted_length=40, endianess='big'):
        hex_value = hex(int.from_bytes(bytes_value, endianess))

        if (len(hex_value[2:]) != excepted_length):
            hex_value = '0x0' + hex_value[2:]

        return hex_value

    def generateTX(self):
        try:
            address = self.textbox_receiver.text()
            if not len(address) == 42:
                raise Exception('Address must have length 42 (beginning with "0x")')

            unitconv = {'wei (atto)':1, 'babbage (femto)':10**3, 'lovelace (pico)':10**6,\
                'shannon (nano)':10**9, 'szabo (micro)':10**12, 'finney (milli)':10**15,\
                'ether':10**18}
            unit = self.combobox_unit.currentText()

            amount = int(float(self.textbox_amount.text().replace(',', '.')) * unitconv[unit])
            if amount < 0:
                raise Exception('Amount must be greated than 0')

            nonce = int(self.textbox_nonce.text())
            if nonce < 0:
                raise Exception('Nonce must be greated than 0')

            gas_price = int(self.textbox_gasprice.text())
            if gas_price < 0:
                raise Exception('Gas price must be greated than 0')

            gas = int(self.textbox_gas.text())
            if gas < 0:
                raise Exception('Gas amount must be greated than 0')

            #data = self.textbox_data.text().encode('utf-8')
            data = self.textbox_data.text()
            
            # try to get data from base16 input
            try:
                ldata = ceil(len(data[2:])/2) if data[:2] == '0x' else ceil(len(data)/2)
                data = int(data, 16).to_bytes(ldata, 'big')
            except ValueError as e:
                data = data.encode('utf-8')

            # from which field do we get the networkid?
            if (self.radiobutton_networkid_textbox.isChecked()):
                # textbox
                networkid = int(self.textbox_networkid.text())
            else:
                # drop down menu
                networkid = int(self.combobox_networkid.currentText()[:2])

            if networkid < 0:
                raise Exception('Network ID must be greated than 0')

            # how to retrieve the private key?
            if (self.radiobutton_key.isChecked()):
                # directly
                priv_key = self.textbox_privatekey.text()

            else:
                # keystore
                keystorefile = self.textbox_keystore.text()
                keystorepw = self.textbox_keystore_pw.text()

                with open(keystorefile, 'r') as kf:
                    jdata = jload(kf)

                priv_key = keys.decode_keystore_json(jdata, keystorepw)
                priv_key = self.safeBytesToHex(priv_key, 64)

            if not len(priv_key) in [64, 66]:
                raise Exception('Invalid private key length: got {}, expected 64 or 66'.format(len(priv_key)))

            #address_sender = hex(int.from_bytes(keys.privtoaddr(priv_key), 'big'))
            address_sender = self.safeBytesToHex(keys.privtoaddr(priv_key), 40)
            self.label_address_sender.setText(address_sender)

            priv_key = int(priv_key, 16)

            # generate the tx data
            tx = Transaction(nonce, gas_price, gas, address, amount, data)
            tx_signed = tx.sign(priv_key)
            tx_data = hex(int.from_bytes(rlpencode(tx_signed), 'big'))
            self.textbrowser_result.setPlainText(str(tx_data))
        except Exception as e:
            print(dir(e))
            self.textbrowser_result.setPlainText('ERROR: \n' + str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    sys.exit(app.exec_())
