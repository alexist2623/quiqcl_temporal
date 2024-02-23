####################### ADC PART #########################

    # Setting input range of each ADC channel, detailed commands are infromed in ADS8698 datasheet page 24 
    # Option 1 : -2.5*V_ref ~ 2.5*V_ref
    # Option 2 : -1.25*V_ref ~ 1.25*V_ref
    # Option 3 : -0.625*V_ref ~ 0.625*V_ref
    # Option 4 : 0 ~ 2.5*V_ref
    # Option 5 : 0 ~ 1.25*V_ref
    # V_ref = 4.096V
    # Strongly recommend to use option 5
        # ADC channel mode setting, detailed commands are infromed in ADS8698 datasheet page 47
from Arty_S7_v1_01 import ArtyS7
import time
import numpy as np
import pandas as pd
from pandas import DataFrame
class ADS8698(ArtyS7):
    # ch=9 using AUX
    def __init__(self,com_port):
        super().__init__(com_port)
    def adc_start(self, adc_ch=0):
        if adc_ch<4:    
            ch_cmd=0xC0+4*adc_ch
        elif adc_ch<8 and adc_ch>=4:
            ch_cmd=0xD0+4*(adc_ch-4)
        elif adc_ch==8:
            ch_cmd=0xE0
        else:
            print('error 내보내기, 잘못된 채널')            
        cmd='ADC START'
        cmd_up = 'UPDATE'
        message=[ch_cmd, 0]
        self.send_command(cmd_up)
        self.send_mod_BTF_int_list(message)
        self.send_command(cmd)
        print(message)
        self.print_msg_bit(message)
        print(cmd)
    
    def adc_stop(self):
        cmd='ADC STOP'
        cmd_up = 'UPDATE'
        self.send_command(cmd_up)
        self.send_command(cmd)
        print(cmd)
        
    def adc_range_select(self, adc_ch=0, option=5):
        ch_cmd=((0x05+adc_ch)<<1)+1
        cmd='ADC RANGE'
        cmd_up = 'UPDATE'
        
        if option==1:
            option_cmd=0
        elif option==2:
            option_cmd=1
        elif option==3:
            option_cmd=2
        elif option==4:
            option_cmd=5
        elif option==5:
            option_cmd=6
                
        message=[ch_cmd,option_cmd]
        self.send_command(cmd_up)
        self.send_mod_BTF_int_list(message)
        self.send_command(cmd)
        print(message)
        self.print_msg_bit(message)
        print(cmd)
        self.adc_start(adc_ch)

    # Transform ADC output style bitstring to voltage
    def adc_voltage_transform(self,v1,v2,v3,option):
        Vref=4.096
        
        if option==2:
            bipolar=True
            Vrange=1.25*Vref
        elif option==3:
            bipolar=True
            Vrange=0.625*Vref
        elif option==4:
            bipolar=False
            Vrange=2.5*Vref
        elif option==5:
            bipolar=False
            Vrange=1.25*Vref
        else:
            bipolar=True
            Vrange=2.5*Vref
        
        
        if bipolar:
            resol=Vrange/2**17
            voltage=(((v1-128)<<10)+(v2<<2)+v3)*resol
        else:
            resol=Vrange/2**18
            voltage=((v1<<10)+(v2<<2)+(v3//64))*resol#v3뒷부분 안나오게 바꿔야할듯
        
        return voltage
    
    def adc_voltage_i_transform(self,voltage, bipolar=False, v_ref=4.096, option=5):
        if bipolar:
            input_code = int(262144/(1.25*v_ref)*voltage)
            if (input_code < -131072) or (input_code > 131071):
                raise ValueError('Error in voltage_out: voltage is out of range')
        
            code = (input_code + 262144) % 262144
        else:
            if voltage < 0:
                raise ValueError('Error in voltage_out: voltage cannot be negative with unipolar setting')
            elif voltage > 262144:
                raise ValueError('Error in voltage_out: voltage cannot be larger than 17.5 V')
            code = int(262144/(v_ref*1.25)*voltage)
            
            if(code>262144):
                raise ValueError('Error in voltage_out: voltage is out of range')  
        print('test:',code)
        return code

    def adc_load_data(self,ch=0,option=5):
        cmd_load='LOAD'
        self.send_command(cmd_load)
        print(cmd_load)
        
        bit_pattern_string = ''
        adcv = self.read_next_message()
        
        for eachByte in adcv[1]:                                ##vivado에 따로 읽을수 있게 만들어놓은 부분을 구현해서 사용해야함
            bit_pattern_string += (format(ord(eachByte), '08b') + ' ')
        print("Bit Pattern : "+bit_pattern_string)
 
        if adcv[0] != '!':
            print('read_adc: Reply is not CMD type:', adcv)
            return False

        # For Analog output(18bit)
        adc_voltage=self.adc_voltage_transform(ord(adcv[1][0]), ord(adcv[1][1]), ord(adcv[1][2]),option)            
        dac_voltage=self.dac_voltage_i_transform(ord(adcv[1][3]), ord(adcv[1][4]))
        print("ADC_RESULT: ",adc_voltage,"\n")  
        print("DAC_RESUTL: ",dac_voltage,"\n")
        return adc_voltage
     
    
        #################### ADC Large data#################
    def adc_load_large_data(self,ch=0,option=5):
        cmd_load='LOAD LARGE'
        self.send_command(cmd_load)
        print(cmd_load)

        adcv = self.read_next_message()
        
        if adcv[0] != '#':   ##tx_buffer2
            print('read_adc: Reply is not CMD type:', adcv)
            return False
        ex_da=[]
        mo_adcv=[]
        for i in range(len(adcv[1])):
            mo_adcv.append(ord(adcv[1][i]))
        
        mo_adcv=np.array(mo_adcv)      
        large_adcv=mo_adcv.reshape(100,3)

        
        print(large_adcv)
        for i in range(len(large_adcv)):     
            voltage=self.adc_voltage_transform(large_adcv[i][0], large_adcv[i][1], large_adcv[i][2],option)            
            ex_da.append([i,voltage])
            print(voltage) 
        #making excel file
        df = DataFrame(ex_da,columns=['time', 'voltage'])
        writer=pd.ExcelWriter('pandastest.xlsx',engine='xlsxwriter')#writer instance
        df.to_excel(writer, sheet_name='Sheet1')#write to excel
        
        workbook=writer.book
        worksheet= writer.sheets['Sheet1']
        
        chart=workbook.add_chart({'type':'line'})#choose data
        
        chart.add_series({'values':'=Sheet1!$C$2:$C$101'})
        worksheet.insert_chart('D2',chart)
        writer.close()
        return 0
    
    
    if __name__ == '__main__':
        if 'adc' in vars(): # To close the previously opened device when re-running the script with "F5"
            adc.close()
        adc = ADS8698('COM28',0)
        adc.print_idn()