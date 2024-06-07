
from datetime import datetime
from dateutil import parser
now = datetime.now()
from time import sleep
import ast, traceback, json, pandas as pd, logging, os
conf = json.load(open("./data/configuration.json"))

tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
expFmt = '%Y-%m-%d'
# expiry = {'NIFTY': ['2024-05-30'], 'BANKNIFTY': ['2024-05-29']}

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
    token_df = token_df.sort_values(by='SEM_EXPIRY_DATE')
    token_df.to_csv(f"./data/api-scrip-master{'_' + tm}.csv", index=False)
    # sleep(1)

class Utils:
    def __init__(self):
        self.master = token_df

    def addTradeStats(self, trd): 
        trd_data = self.getTradeDetails(trd['trade_id'])
        dict_trd = {'index': trd['index'], 'trade_id': trd['trade_id'], 
                        'sl': trd['sl'], 'target': trd['target']}
        if trd_data is None:
            
            self.updateTradeDetails(dict_trd, act='add')
        else:
            self.deleteTradeStats(dict_trd['trade_id'])
            self.updateTradeDetails(dict_trd, act='add')


    def deleteTradeStats(self, trade_id): 
        res = self.getTradeDetails(trade_id)
        if res is not None:
            self.updateTradeDetails(res, act='delete')

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

    def pnlCleanup(self, trades):
        trd_data = []
        with open("./data/pnl.txt", "r") as fileStore:
            trd_data = fileStore.readline()
            fileStore.close()
        if isinstance(trd_data, str) and trd_data.strip() != "": 
            trd_data = ast.literal_eval(trd_data)
        else: trd_data = []
        for _trd in trd_data:
            if int(_trd['trade_id']) in trades: trd_data.remove(_trd)

    def updateTradeDetails(self, trade_details, act=None):
        trd_data = []
        with open("./data/pnl.txt", "r") as fileStore:
            trd_data = fileStore.readline()
            fileStore.close()
        if isinstance(trd_data, str) and trd_data.strip() != "": 
            trd_data = ast.literal_eval(trd_data)
        else: trd_data = []
        if act=='add':
            trd_data.append(trade_details)
        if act=='delete':
            trd_data.remove(trade_details)
        try:
            with open("./data/pnl.txt", "w") as fileStore:
                fileStore.write(str(trd_data))
                fileStore.close()              
        except Exception:
            print(traceback.format_exc())
            logger.error(f"utils, updateTradeDetails {traceback.format_exc()}")

    def securityId(self, index, strike, option, exp_num=1):
        exp_cnt = 0
        if exp_num == 0: exp_num = 1
        df = self.master
        df = df[df['INDEX'] == index]
        df = df[df['SEM_OPTION_TYPE'] == option]
        df = df[df['SEM_STRIKE_PRICE'] == strike]
        for ind in df.index:
            exp_dt = df['SEM_EXPIRY_DATE'][ind]
            exp_dt = self.getDateExpFrmt(exp_dt)
            sys_dt = self.getDate(expFmt)
            if exp_dt >= sys_dt:
                exp_cnt = exp_cnt + 1
                if exp_cnt == exp_num:
                    s_id = str(df['SEM_SMST_SECURITY_ID'][ind])
                    symbol = df['SEM_CUSTOM_SYMBOL'][ind]
                    return {'s_id': s_id, 'symbol': symbol} if int(s_id) > 0 else {'s_id': '-1', 'symbol': '--'}
    
    def getDate(self, fmt=None):
        if fmt is None: return datetime.now().strftime("%m-%d-%Y")
        else: return datetime.now().strftime(fmt)
    def getDateExpFrmt(self, dt_str):
        # print(dt_str)
        # print(expFmt)
        return parser.parse(dt_str).strftime(expFmt)
    def getTime(self):
        return datetime.now().strftime("%H:%M:%S")
    def getDateTime(self):
        return datetime.now().strftime("%d/%m/%Y, %H:%M:%S %p")
    def dictToDataFrame(self):
        return datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    
if __name__ == "__main__":
    print("Utils Processing")
    ut = Utils()
    sid = ut.securityId('BANKNIFTY', '49200', 'CE', 1)
    print(sid)
    #     strike = ScripCode["SEM_SMST_SECURITY_ID"]
    # print("ScripCode: ", strike)
    # exit()