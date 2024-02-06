"""
Created on Wed Sep 1 22:52:01 2021

@author: jhjeong
E-mail: jhjeong32@snu.ac.kr
Tel. 010-9600-3392
"""
from PyQt5.QtCore import QIODevice, QByteArray, QDataStream, pyqtSignal
from PyQt5.QtNetwork import QTcpSocket

class ClientSocket(QTcpSocket):
    
    device_dict = {}
    conn_buffer = []
    _message_signal = pyqtSignal(list)
    _break_con_signal = pyqtSignal(bool)
    
    def __init__(self, parent, user_name):
        super().__init__()
        self._block_size = 0
        self.user_name = user_name
        
        self.readyRead.connect(self.receiveMessage)
        self.disconnected.connect(self.breakConnection)
        self.isConnected = False

    def makeConnection(self, host, port):
        self.connectToHost(host, int(port), QIODevice.ReadWrite)
        
        # Waits until the socket is connected, up to 1000 ms.
        # If it fails to connect to the server, then returns -1
        if(self.waitForConnected(1000) != True):
            return -1

        # Sends CON message to notify the name of the user
        message = ['C', 'SRV', 'CON', [self.user_name]]
        self.sendMessage(message)
        self.isConnected = True
        return 0

    def breakConnection(self, spontaneous=False):
        if spontaneous:
            message = ['C', 'SRV', 'DCN', [self.user_name]]
            self.sendMessage(message)
            self.disconnectFromHost()
            print("Disconnected from the server.")
        self._break_con_signal.emit(self.state())  # This will reset the status of the devices.
        self.isConnected = False    
        
    def checkConnection(self):
        print(self.state())
        self._break_con_signal.emit(self.state())

        
    def checkHardState(self):
        message = ["Q", "SRV", "CON", []]
        self.sendMessgae(message)

    def sendMessage(self, msg):
        if not self.isOpen():
            return -1

        block = QByteArray()
        output = QDataStream(block, QIODevice.WriteOnly)
        output.setVersion(QDataStream.Qt_5_0)

        output.writeUInt16(0)
        output.writeQString(msg[0])         ### flag C/S
        output.writeQString(msg[1])         ### device; 3 ~ 4 charaters
        output.writeQString(msg[2])         ### command of 3 or 4 characters
        output.writeQVariantList(msg[3])    ### data
        output.device().seek(0)
        output.writeUInt16(block.size()-2)

        self.write(block)

    def receiveMessage(self):

        stream = QDataStream(self)
        stream.setVersion(QDataStream.Qt_5_0)
        while(self.bytesAvailable() >= 2):
            if self._block_size == 0:
                if self.bytesAvailable() < 2:
                    return
                self._block_size = stream.readUInt16()
            if self.bytesAvailable() < self._block_size:
                return
            try:
                control = str(stream.readQString())     ### flag C/S
                device  = str(stream.readQString())     ### command of 3 or 4 characters
                command = str(stream.readQString())     ### command of 3 or 4 characters
                data = list(stream.readQVariantList())   ### data
                self._block_size = 0
                
                self._message_signal.emit([control, device, command, data])
                self.my_data = [control, device, command, data]

            except:
                pass


# if __name__ == "__main__":
    # client = ClientSocket(None, "test")
    # from PyQt5.QtNetwork import QHostAddress
    # client.makeConnection(QHostAddress(QHostAddress.LocalHost), 55555)
