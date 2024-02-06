# -*- coding: utf-8 -*-
"""
Created on Mon May 24 18:15:02 2021

@author: QCP32
"""
import psycopg2
import datetime
import os
import pandas.io.sql as pdsql

db_ip   = '172.22.22.100'
db_port = '5432'
db_name = 'asri133109'
db_user = 'postgres'
db_pw   = '171Yb+postgres'


class DB_ASRI133109():
    """
    This class is to provide a convinient way to record experimental data
    Requirement: psycopg2.
    If you don't remember the id of the chamber and table, check
    https://docs.google.com/presentation/d/1tbztx5L5tOkG60qyiP2rs8Ac7x69O7xCoiF9odYLXUk/edit#slide=id.p
        
    Containing methods are
    - asri_ht: Tempeerature and humidity of the lab.
    - asri_oven: Oven current, voltage and resistance.
    - asri_traprf: Trap RF amplitude, frequency and those of reflected one.
    - asri_rabi: Resonance frequency of the clock state and Rabi period.
    """
    
    def __init__(self):
        super().__init__()
        self.version   = os.path.basename(__file__)[-7:-3].replace("_", ".")
        self.__db_ip   = db_ip
        self.__db_port = db_port
        self.__db_name = db_name
        self.__db_user = db_user
        self.__db_pw   = db_pw
        
        self._connect_to_db()
        self._conn_flag = False
        print("version:", self.version)
        
    def _connect_to_db(self):
        try:
            self._conn = psycopg2.connect(database=self.__db_name,
                                         host=self.__db_ip,
                                         port=self.__db_port,
                                         user=self.__db_user,
                                         password=self.__db_pw,
                                         connect_timeout = 1)
            self._conn_flag = True
        except:
            print("Couldn't connect to the DB server.")
        
    def _disconnect_from_db(self):
        self._conn.close()
        self._conn_flag = False
        
    def _get_columns(self, tbl_name):
        df = pdsql.read_sql_query("select * from %s limit 0;" % tbl_name, self._conn)
        return list(df)
    
    def _to_string(self, args):
        string_list = []
        for val in args:
            if type(val) == str:
                string_list.append('\'' + val + '\'')
            else:
                string_list.append(str(val))
        return string_list       
        
    def _into_DB(func):
        def db_wrapper(self, *args):
            if self.__conn_flag:
                curs = self._conn.cursor()
                tbl_columns = self._get_columns(func.__name__)
                tbl_values = self._to_string(args)
                
                
                if 'time' in tbl_columns:
                    time2db = datetime.datetime.now().strftime("\'%Y-%m-%d %H:%M:%S\'")
                    tbl_columns.sort(key='time'.__eq__)
                    tbl_values.append(time2db)
                    
                header = "insert into %s" % func.__name__
                insert_columns = ", ".join(tbl_columns)
                insert_values = ", ".join(tbl_values)
    
                db_string = header + "(" + insert_columns + ")" + " values " + "(" + insert_values + ")"
                curs.execute(db_string)
                
                self._conn.commit()
                print("Commited to %s" % func.__name__)
                
                return func
        db_wrapper.__name__ = func.__name__
        db_wrapper.__doc__ = func.__doc__
        return db_wrapper
        
        
    @_into_DB
    def asri_ht(self, table_number: int, sensor_number: str, humidity: float, temperature: float):
        '''
        asri_ht(table_number: int, sensor_number: str, humidity: float, temperature: float)
        
        Contents)
            Column     |            Type             |
        ---------------+-----------------------------+
         table_number  | integer                     |
         sensor_number | character varying(4)        |
         time          | timestamp without time zone |
         humidity      | real                        |
         temperature   | real                        |
        
        Example)
        - table_number: 2
        - sensor_number: 'IN2'
        - humidity: 32.5
        - temperature: 21.7
        '''
        return
        
    @_into_DB
    def asri_oven(self, ch_id: str, ion: str, resistance: float, vol: float, curr: float):
        '''
        asri_oven(ch_id: str, ion: str, resistance: float, voltage, float, current: float)
        
        Resistance in Ω, voltage in V, current in A.
        
        Contents)
           Column   |            Type             |
        ------------+-----------------------------+
         ch_id      | character varying(6)        |
         ion        | character varying(10)       |
         time       | timestamp without time zone |
         resistance | real                        |
         voltage    | real                        |
         current    | real                        |
        
        Example)
        - ch_id: 'D1'
        - ion: '174yb'
        - resistance: 0.921
        - voltage: 0.848
        - current: 0.781
        '''
        return
    
    @_into_DB
    def asri_traprf(self, ch_id: str, rf_amp, float, rf_freq: float, rfl_amp: float, smpl_amp: float):
        '''
        asri_traprf(ch_id: str, rf_amp, float, rf_freq: float, rfl_amp: float, smpl_amp: float)
        
        rf_amp is Vpp from SG, rf_freq in Hz from SG.
        rfl_amp is the reflected signal amplitude Vpp from oscilloscope.
        smpl_amp is the sampled forward RF amplitude Vpp from oscillocope.
        
        Contents)
          Column  |            Type             |
        ----------+-----------------------------+
         ch_id    | character varying(6)        |
         time     | timestamp without time zone |
         rf_amp   | real                        |
         rf_freq  | real                        |
         rfl_amp  | real                        |
         smpl_amp | real                        |

        Example)
        - ch_id: "D1"
        - rf_amp: 0.19
        - rf_freq: 23216332
        - rfl_amp: 0.025
        - smpl_amp: 0.250
        '''
        return
    
    @_into_DB
    def asri_rabi(self, ch_id: str, coil_current: float, mw_dbm: float, mw_freq: float, rabi_period: float):
        '''
        asri_rabi(ch_id: str, coil_current: float, mw_dbm: float, mw_freq: float, rabi_period: float)
        
        coil_current in A, mw_dbm in dbm, mw_freq in Hz, rabi_period in sec.
        
            Column    |            Type             |
        --------------+-----------------------------+
         ch_id        | character varying(4)        |
         time         | timestamp without time zone |
         coil_current | real                        |
         mw_dbm       | real                        |
         mw_freq      | double precision            |
         rabi_period  | double precision            |

        Example)
        - ch_id: "D1"
        - coil-current: 3
        - mw_dbm: 13
        - mw_freq: 12642818216.32
        - rabi_period: 0.0001827482738
        '''
    
    @_into_DB
    def asri_test2(ch_id: str, value: float):
        return
        
    
    
if __name__ == "__main__":
    if 'my_db' in vars():
        my_db._disconnect_from_db()
    my_db = DB_ASRI133109()
    