# -*- coding: utf-8 -*-
"""
Created on Tue Feb 27 14:58:01 2024

@author: alexi
"""

from sipyco.pc_rpc import Client

def main():
    ad9912_0 = Client("::1", 1001, "ad9912_0")
    ad9912_vva = Client("::1", 1001, "ad9912_vva")
    try:
        ad9912_0.test()
        ad9912_vva.test_vva()
    finally:
        ad9912_0.close_rpc()
        ad9912_vva.close_rpc()

if __name__ == "__main__":
    main()