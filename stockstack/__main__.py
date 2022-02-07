import logging

from stockstack.network.gateway import Gateway
from stockstack.settings import Settings
from stockstack.world.market import Market

_BANNER = """\
 #####                             
#     # #####  ####   ####  #    # 
#         #   #    # #    # #   #  
 #####    #   #    # #      ####   
      #   #   #    # #      #  #   
#     #   #   #    # #    # #   #  
 #####    #    ####   ####  #    # 
                                   
 #####                             
#     # #####   ##    ####  #    # 
#         #    #  #  #    # #   #  
 #####    #   #    # #      ####   
      #   #   ###### #      #  #   
#     #   #   #    # #    # #   #  
 #####    #   #    #  ####  #    # \
"""


def run():
    Settings.logger.debug(f"Starting")
    Settings.load()

    market = Market(Settings.get()["database"])
    market.start()

    gateway = Gateway({**market.dbinfo, "options": f"-c search_path={Settings.get()['stockstack']['schema']}"},
                      Settings.get()["stockstack"]["wssocket"])

    gateway.run()  # blocking


if __name__ == "__main__":
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    stderrLogger = logging.StreamHandler()
    stderrLogger.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
    logger.addHandler(stderrLogger)
    Settings.logger = logger
    # print(_BANNER)
    run()
