class fiberSW:
    def __init__(self, com):
        self.com = com

    def switchChannel(self, ch):
        chString = 'ch%1d\r\n' % ch
        print(chString)
        self.com.write(chString.encode('UTF-8'))
       # print chString
        
