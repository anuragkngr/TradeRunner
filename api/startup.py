import ast, traceback, numpy as np, json, threading
conf = json.load(open("./data/configuration.json"))
from datetime import datetime, time
from utils import Utils
from time import sleep
# from trade_book import TradeBook
from tabulate import tabulate, SEPARATING_LINE
# from order_management_system import OMS
# from SmartApi.smartWebSocketV2 import SmartWebSocketV2
# totp = pyotp.TOTP(conf['token']).now()
# correlation_id = 'anurag-test'
# smartApi = SmartConnect(conf['api_key'])
# data = smartApi.generateSession(conf['user_id'], conf['mpin'], totp)
# jwt_token = data['data']['jwtToken']
# reftoken = data['data']['refreshToken']
# feedToken = smartApi.getfeedToken()
trade_headers=['SYMBOL', 'POSITION', 'QTY', 'PRICE', 'LTP', 'P&L', 'REALISED']
# trade_headers=['SCRIP_CODE', 'SYMBOL', 'QTY', 'PRICE', 'AVG_PRICE', 'LTP', 'P&L', 'REALISED', 'UNREALISED']
# headers=['SCRIP_CODE', 'SYMBOL', 'QTY', 'PRICE', 'AVG_PRICE', 'LTP', 'P&L', 'REALISED', 'UNREALISED']
# sws = SmartWebSocketV2(jwt_token, conf['api_key'], conf['user_id'], feedToken,max_retry_attempt=0, retry_strategy=0, retry_delay=10, retry_duration=30)
# exp_format = '%m/%d/%Y %H:%M'
# util = Utils()
# curVal = (abs(float(po['netqty'])*(float(po['ltp']))))
                    # if int(po['netqty']) < 0:
                    #     pos['netprice'] = pos['avgnetprice'] = abs((curVal + float(po['unrealised'])) / (float(po['netqty'])))
                    # else: pos['netprice'] = pos['avgnetprice'] = abs((curVal - float(po['unrealised'])) / (float(po['netqty'])))
# indx = ['NIFTY','BANKNIFTY','FINNIFTY']
# mas = pd.read_csv("./data/scripmaster-csv-format.csv")
# idx_list = [{'name':'NIFTY', 'value':'999920000'}, {'name':'BANKNIFTY', 'value':'999920005'}, {'name':'FINNIFTY', 'value':'999920041'}]
# fut_list = {'NIFTY':'52222', 'BANKNIFTY':'52220', 'FINNIFTY':'35051'}
# idx_set = {'NIFTY':'999920000', 'BANKNIFTY':'999920005', 'FINNIFTY':'999920041'}
# idx_fut_may = [46930, 46923, 35089];
# idx_fut_jun = [35004, 35020, 35152];
# strike_range = 20

# df = pd.DataFrame(mas)
# df = df.loc[df['Exch'] == 'N']
# index_df = df.loc[(df['Name'].isin(indx))]
# df = df.loc[df['ExchType'] == 'D']
# df = df.loc[df['ISIN'].isin(indx)]
# feture_df = df.loc[df['CpType'] == 'XX']
# option_df = df.loc[(df['CpType'].isin(['CE', 'PE']))]
# now = datetime.now()
# cred={
#     "APP_NAME": conf["app_name"],
#     "APP_SOURCE": conf["app_source"],
#     "USER_ID": conf["user_id"],
#     "PASSWORD": conf["password"],
#     "USER_KEY": conf["user_key"],
#     "ENCRYPTION_KEY": conf["exception_key"]
#     }

# tm = now.strftime("%d") + "-" + now.strftime("%B") + "-" + now.strftime("%Y") + "-" + now.strftime("%A") + "-"  + now.strftime("%H-%M")
# logging.basicConfig(
#     level=logging.INFO,
#     filename=f"./data/logs/application_{tm}.log",
#     # filename=f"./data/logs/application_{tm}.log",
#     filemode="w",
#     format="%(asctime)s - %(levelname)s - %(message)s",
# )

# if data['status'] == False:
#     logger.error(data)

# class Startup:
    # def __init__(self):
        # self.sws = SmartWebSocketV2(jwt_token, conf['api_key'], conf['user_id'], feedToken,max_retry_attempt=0, retry_strategy=0, retry_delay=10, retry_duration=30)
        # self.data = smartApi.generateSession(conf['user_id'], conf['mpin'], totp)
        # self.logger = logging.getLogger()
        # self.cred = cred
        # self.index_df = index_df
        # self.feture_df = feture_df
        # self.option_df = option_df
        # self.conf = conf
        # self.strike_range = strike_range
        # self.idx_list = idx_list
        # self.fut_list = fut_list
        # self.idx_set = idx_set

if __name__ == "__main__":
    print("Starup Processing start.")
    # start = Startup()
    # print(feture_df)
    # expiry = ''
    # for ind, row in feture_df.fillna("").iterrows():
    #         expiry = row["Expiry"]#expiry
    #         print(expiry)
    




#// TODO: manage exiting trades => get market price, options price, update price
#// TODO: manage trades (Multiples), move entry condition chech in configuration
#// TODO:create new trade => check market status, time (open close), 
#// TODO: create strangle and manage it. 
#// TODO: Analyse market (find right index and trategy to trade)
#// TODO: get ScripCode, quantity and place order
#// TODO: create order, trade object and add to trade book.
#// TODO: update trade quantity.
#// TODO: reporting.