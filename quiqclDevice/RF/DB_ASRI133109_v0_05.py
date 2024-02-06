# -*- coding: utf-8 -*-
"""
v0_03: asri_dc added.
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
    This class is to provide a convenient way to record experimental data to the DB.
    A wrapper function that automatically converts from python strings to strings for DB.
    
    Requirement: psycopg2.
    If you don't remember the id of chambers and tables, check
    https://docs.google.com/presentation/d/1tbztx5L5tOkG60qyiP2rs8Ac7x69O7xCoiF9odYLXUk/edit#slide=id.p
        
    Containing methods are
    - asri_ht: Tempeerature and humidity of the lab.
    - asri_oven: Oven current, voltage and resistance.
    - asri_traprf: Trap RF amplitude, frequency and those of reflected one.
    - asri_rabi: Resonance frequency of the clock state and Rabi period.
    - asri_outage: Time of the event, power shut down flag, network condition at that time.
    """
    
    def __init__(self, timeout=2, auto_connect=True):
        self._version   = os.path.basename(__file__)[-7:-3].replace("_", ".")
        self.__db_ip   = db_ip
        self.__db_port = db_port
        self.__db_name = db_name
        self.__db_user = db_user
        self.__db_pw   = db_pw
        self._timeout = timeout
        
        if auto_connect:
            try:
                self._connect_to_db()
            except:
                raise RuntimeError ("Couldn't connect to the DB server.")
        
    @property
    def version(self):
        return self._version
        
    def __call__(self):
        print(self.__doc__)
        
    def _connect_to_db(self):
        self._conn = psycopg2.connect(database=self.__db_name,
                                     host=self.__db_ip,
                                     port=self.__db_port,
                                     user=self.__db_user,
                                     password=self.__db_pw,
                                     connect_timeout = self._timeout)
        print("version:", self._version)
        
    def _disconnect_from_db(self):
        self._conn.close()
        
    def _get_columns(self, tbl_name="", limit=0):
        df = pdsql.read_sql_query("select * from %s limit %d;" % (tbl_name, limit), self._conn)
        return list(df)
    
    def _get_data(self, string=""):
        df = pdsql.read_sql_query(string, self._conn)
        return df
    
    def _to_string(self, args):
        string_list = []
        for val in args:
            if type(val) == str:
                string_list.append('\'' + val + '\'')
            else:
                string_list.append(str(val))
        return string_list       
    
    def _to_string_kargs(self, kargs):
        tbl_columns = list(kargs.keys())
        tbl_values  = list(kargs.values())
        for idx, tbl_value in enumerate(tbl_values):
            if type(tbl_value) == str:
                tbl_values[idx] = '\'' + tbl_value + '\''
            else:
                tbl_values[idx] = str(tbl_value)
        
        return (tbl_columns, tbl_values)
        
                
    def _into_DB(func):
        def db_wrapper(self, *args, **kargs):
            curs = self._conn.cursor()
            if args:
                tbl_columns = self._get_columns(func.__name__)
                tbl_values = self._to_string(args)
                                            
            elif kargs:
                tbl_columns, tbl_values = self._to_string_kargs(kargs)
                if 'time' in self._get_columns(func.__name__):
                    tbl_columns.append('time')
                    
            if 'time' in tbl_columns:
                time2db = datetime.datetime.now().strftime("\'%Y-%m-%d %H:%M:%S\'")
                tbl_columns.sort(key='time'.__eq__)
                
                if "custom_time" in kargs.keys():
                    tbl_columns.append("\'" + kargs["custom_time"] + "\'")
                else:
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
    def asri_oven(self, ch_id: str, ion: str, resistance: float, voltage, float, current: float):
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
    def asri_traprf(self, ch_id: str, rf_amp, float, rf_freq: float, fwd_amp: float, rfl_amp: float):
        '''
        asri_traprf(ch_id: str, rf_amp, float, rf_freq: float, fwd_amp: float, rfl_amp: float)
        
        rf_amp is Vpp from SG, rf_freq in Hz from SG.
        fwd_amp is the forward RF amplitude Vpp from oscillocope.
        rfl_amp is the reflected signal amplitude Vpp from oscilloscope.
        
        Contents)
          Column  |            Type             |
        ----------+-----------------------------+
         ch_id    | character varying(6)        |
         time     | timestamp without time zone |
         rf_amp   | real                        |
         rf_freq  | real                        |
         fwd_amp  | real                        |
         rfl_amp  | real                        |

        Example)
        - ch_id: "D1"
        - rf_amp: 0.19
        - rf_freq: 23216332
        - fwd_amp: 0.250
        - rfl_amp: 0.025
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
        return
    
    @_into_DB
    def asri_dc(self, ch_id='ch_id', l1 =0, l2 =0, l3 =0, l4 =0, l5 =0, l6 =0, l7 =0, l8 =0, l9 =0, l10=0,
                                     l11=0, l12=0, l13=0, l14=0, l15=0, r1 =0, r2 =0, r3 =0, r4 =0, r5 =0,
                                     r6 =0, r7 =0, r8 =0, r9 =0, r10=0, r11=0, r12=0, r13=0, r14=0, r15=0,
                                     il =0, ir =0):
        '''
        !!! NOTE !!!
        This method accepts keyword arguments, you need to specify columns that you want to commit.
        DC voltage values are in V, il and ir are inner DCs.        
                
         Column |            Type             | Collation | Nullable | Default
        --------+-----------------------------+-----------+----------+---------
         ch_id  | character varying(6)        |           |          |
         time   | timestamp without time zone |           |          |
         l1     | real                        |           |          |
         l2     | real                        |           |          |
         l3     | real                        |           |          |
         l4     | real                        |           |          |
         l5     | real                        |           |          |
         l6     | real                        |           |          |
         l7     | real                        |           |          |
         l8     | real                        |           |          |
         l9     | real                        |           |          |
         l10    | real                        |           |          |
         l11    | real                        |           |          |
         l12    | real                        |           |          |
         l13    | real                        |           |          |
         l14    | real                        |           |          |
         l15    | real                        |           |          |
         r1     | real                        |           |          |
         r2     | real                        |           |          |
         r3     | real                        |           |          |
         r4     | real                        |           |          |
         r5     | real                        |           |          |
         r6     | real                        |           |          |
         r7     | real                        |           |          |
         r8     | real                        |           |          |
         r9     | real                        |           |          |
         r10    | real                        |           |          |
         r11    | real                        |           |          |
         r12    | real                        |           |          |
         r13    | real                        |           |          |
         r14    | real                        |           |          |
         r15    | real                        |           |          |
         il     | real                        |           |          |
         ir     | real                        |           |          |
        
        Example)
        - ch_id="EC"
        - l1 = 0
        - l2 = 0.69
        - l3 = 0.69
        - l4 = -0.68
        - l5 = -0.68
        - l6 = 0.21
        - l7 = 0.21
        - r1 = 0
        - r2 = 0.92
        - r3 = 0.92
        - r4 = -0.46
        - r5 = -0.46
        - r6 = 0.43
        - r7 = 0.43
        - il = 1.31
        - ir = 0.91
        '''
        return
    
    @_into_DB
    def asri_outage(self, custom_time:str, power:bool, ethernet:bool):
        '''
        asri_outage(custom_time:yyyy-mm-dd HH:MM:SS, power:bool, ethernet:bool)
        
        The custom_time is when the blackout happened.
        The power False means a power outage has happend.
        The ethernet flag indicates whether the ethernet is dead at that time.
        When the ethernet died with the power outage, the whole lab may have been shut down.
                
            Column    |            Type             |
        --------------+-----------------------------+
         custom_time  | timestamp without time zone |
         power        | boolean                     |
         ethernet     | boolean                     |

        Example)
        - custom_time: "2019-11-01 13:22:05"
        - power: False
        - ethernet: True
        '''
        return
    
    @_into_DB
    def asri_mira(self, ch_id:str, current:float, power:float):
        '''
        asri_mira(ch_id:str, current:float, power:float)
        
        The ch_id is in case when we have multiple mira lasers.
        I assigned the first mira one as ENT1
        The current is of the diode.
        The power is not decided yet where to measure
        
         Column  |            Type             |
        ---------+-----------------------------+
         ch_id   | character varying(6)        |
         time    | timestamp without time zone |
         current | real                        |
         power   | real                        |
        
        Example)
        - ch_id: "ENT1"
        - current: 0.03
        - power: 0.000003
        
        '''
        return
        
    
    
if __name__ == "__main__":
    if 'my_db' in vars():
        my_db._disconnect_from_db()
    my_db = DB_ASRI133109()
    