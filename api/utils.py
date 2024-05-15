import ast, traceback, json, pandas as pd, logging, os
conf = json.load(open("./data/configuration.json"))
from datetime import datetime, date
from time import sleep
# from market_feed import read
expiry = {'NIFTY': ['2024-05-16', '2024-05-23', '2024-05-30', '2024-06-06'], 
          'BANKNIFTY': ['2024-05-15', '2024-05-22', '2024-05-29', '2024-06-05'], 
          'FINNIFTY': ['2024-05-14', '2024-05-21', '2024-05-28', '2024-06-04'], 
          'SENSEX': ['2024-05-10', '2024-05-17', '2024-05-24', '2024-05-31'], 
          'BANKEX': ['2024-05-13', '2024-05-17', '2024-05-27', '2024-06-03']}
now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
os.makedirs(f"./logs/{tm}", exist_ok=True)
os.makedirs(f"./data/", exist_ok=True)
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application.log",
    filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
token_df = None
url = 'https://images.dhan.co/api-data/api-scrip-master.csv'
try:
    token_df = pd.read_csv(f"./data/api-scrip-master{'_' + tm}.csv")
except Exception:
    token_df = pd.read_csv(url)
    token_df = token_df[(token_df['SEM_INSTRUMENT_NAME'] == 'OPTIDX') | (token_df['SEM_INSTRUMENT_NAME'] == 'INDEX')]
    token_df['SEM_EXPIRY_DATE'] = pd.to_datetime(token_df['SEM_EXPIRY_DATE'], format = 'mixed').apply(lambda x: x.date())
    token_df['INDEX'] = [str(scrip).split('-')[0] for scrip in token_df['SEM_TRADING_SYMBOL']]
    token_df.to_csv(f"./data/api-scrip-master{'_' + tm}.csv", index=False)

class Utils:
    def __init__(self):
        self.master = token_df

    def updateTradeStats(self, trd): 
        dict_trd = trd.to_dict_obj()
        res = self.getTradeDetails(dict_trd['trade_id'])
        if res is not None:
            self.updateTradeDetails(res)

    def updateTrade(self, trd): 
        trd_data = {}; dict_trd = trd.to_dict_obj()
        res = self.getTradeDetails(dict_trd['trade_id'])
        if res is None:
            trade_details = {'index': dict_trd['index'],'trade_id': dict_trd['trade_id'], 
                             'strategy': dict_trd['strategy'],'margin': dict_trd['margin'], 
                             'sl': dict_trd['sl'],'target': dict_trd['target']}#,
                            #  'max': dict_trd['max'],'min': dict_trd['min']}
            self.updateTradeDetails(trade_details, True)
        else:
            trd.strategy = dict_trd['strategy'] = res['strategy']
            trd.margin = dict_trd['margin'] = res['margin']
            trd.sl = dict_trd['sl'] = res['sl']
            trd.target = dict_trd['target'] = res['target']
            # trd.pnlMax = dict_trd['pnlMax'] = res['max']
            # trd.pnlMin = dict_trd['pnlMin'] = res['min']

        with open("./data/margin.txt", "r") as fileStore:
            trd_data = fileStore.readline()
            fileStore.close()
        if isinstance(trd_data, str) and trd_data.strip() != "": 
            trd_data = ast.literal_eval(trd_data)
        else: trd_data = {'NIFTY': {'margin': 0, 'trades': []}, 'BANKNIFTY': {'margin': 0, 'trades': []}, 
                          'FINNIFTY': {'margin': 0, 'trades': []}, 'NIFTYMCAP50': {'margin': 0, 'trades': []}, 
                          'SENSEX': {'margin': 0, 'trades': []}, 'BANKEX': {'margin': 0, 'trades': []}}
        
        trades = trd_data[trd.index]['trades']
        _trades = trades.copy()
        flag = False
        if trades:
            flag = True
            for t in _trades:
                if t['trade_id'] == trd.trade_id:
                    trades.remove(t)
                    trades.append(trd.to_dict_obj())
                    #  trd_data[trd.index]['trades'][str(trd.trade_id)] = trd.to_dict_obj()
                    flag = False
                    break
        else: trd_data[trd.index]['trades'].append(trd.to_dict_obj())
        if flag: trd_data[trd.index]['trades'].append(trd.to_dict_obj())

        try:
            with open("./data/margin.txt", "w") as fileStore:
                fileStore.write(str(trd_data))
                fileStore.close()
        except Exception:
            print(traceback.format_exc())
            logger.error(f"trade book, updateTrade {traceback.format_exc()}")

    def getTradeDetails(self, trade_id):
        trd_data = []
        with open("./data/pnl.txt", "r") as fileStore:
            trd_data = fileStore.readline()
            fileStore.close()
        if isinstance(trd_data, str) and trd_data.strip() != "": 
            trd_data = ast.literal_eval(trd_data)
        else: trd_data = []
        for _trd in trd_data:
            if _trd['trade_id'] == trade_id:
                return _trd  
        return None      

    def updateTradeDetails(self, trade_details, add=False):
        trd_data = []
        with open("./data/pnl.txt", "r") as fileStore:
            trd_data = fileStore.readline()
            fileStore.close()
        if isinstance(trd_data, str) and trd_data.strip() != "": 
            trd_data = ast.literal_eval(trd_data)
        else: trd_data = []
        if add:
            trd_data.append(trade_details)
        else:
            for trd in trd_data:
                if trd['trade_id'] == trade_details['trade_id']:
                    trd['strategy'] = trade_details['strategy']
                    trd['margin'] = trade_details['margin']
                    trd['sl'] = trade_details['sl']
                    trd['target'] = trade_details['target']
                    # trd['max'] = trade_details['max']
                    # trd['min'] = trade_details['min']
        try:
            with open("./data/pnl.txt", "w") as fileStore:
                fileStore.write(str(trd_data))
                fileStore.close()              
        except Exception:
            print(traceback.format_exc())
            logger.error(f"utils, updateTradeDetails {traceback.format_exc()}")
                
    def securityId(self, index, strike, option, exp_num=1):
        df = self.master
        exp = expiry[index][exp_num - 1]
        df = df[(df['INDEX'] == index) & (df['SEM_OPTION_TYPE'] == option) & 
            (df['SEM_STRIKE_PRICE'] == strike) & (df['SEM_EXPIRY_DATE'] == exp)]
        return df['SEM_SMST_SECURITY_ID'].values[0] if len(df) == 1 else -1

    def read(self):
        try:
            with open(f"./logs/{tm}/market_feed.txt", "r") as fileStore:
                trd_data = fileStore.readline()
                fileStore.close()
                if isinstance(trd_data, str) and trd_data.strip() != "": 
                    trd_data = ast.literal_eval(trd_data)
        except Exception:
            print(traceback.format_exc())
            logger.error(f"Market Feed , read {traceback.format_exc()}")
            try:
                sleep(1)
                with open(f"./logs/{tm}/market_feed.txt", "r") as fileStore:
                    trd_data = fileStore.readline()
                    fileStore.close()
                    if isinstance(trd_data, str) and trd_data.strip() != "": 
                        trd_data = ast.literal_eval(trd_data)
            except Exception:
                print(traceback.format_exc())
                logger.error(f"Market Feed , read 2 {traceback.format_exc()}")
        return trd_data
    
if __name__ == "__main__":
    print("Utils Processing")
    ut = Utils()
    sid = ut.securityId('BANKNIFTY', '49200', 'CE', 1)
    print(sid)
    #     strike = ScripCode["SEM_SMST_SECURITY_ID"]
    # print("ScripCode: ", strike)
    # exit()