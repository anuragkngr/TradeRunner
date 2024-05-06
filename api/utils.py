import ast, traceback, json, pandas as pd, logging, os
conf = json.load(open("./data/configuration.json"))
from datetime import datetime, date
from time import sleep
expiry = {'NIFTY': ['2024-05-09', '2024-05-16', '2024-05-23', '2024-05-30', '2024-06-06'], 
          'BANKNIFTY': ['2024-05-08', '2024-05-15', '2024-05-22', '2024-05-29', '2024-06-05'], 
          'FINNIFTY': ['2024-05-07', '2024-05-14', '2024-05-21', '2024-05-28', '2024-06-04'], 
          'SENSEX': ['2024-05-03', '2024-05-10', '2024-05-17', '2024-05-24', '2024-05-31'], 
          'BANKEX': ['2024-05-06', '2024-05-13', '2024-05-17', '2024-05-27', '2024-06-03']}
now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
os.makedirs(f"./logs/{tm}", exist_ok=True)
os.makedirs(f"./data/", exist_ok=True)
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application.log",
    filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
class Utils:

    def __init__(self):
        try:
            self.master = pd.read_csv(f"./data/api-scrip-master{'_' + tm}.csv")
        except:
            url = 'https://images.dhan.co/api-data/api-scrip-master.csv'
            token_df = pd.read_csv(url)
            token_df = token_df[(token_df['SEM_INSTRUMENT_NAME'] == 'OPTIDX') | (token_df['SEM_INSTRUMENT_NAME'] == 'INDEX')]
            token_df['SEM_EXPIRY_DATE'] = pd.to_datetime(token_df['SEM_EXPIRY_DATE'], format = 'mixed').apply(lambda x: x.date())
            token_df['INDEX'] = [str(scrip).split('-')[0] for scrip in token_df['SEM_TRADING_SYMBOL']]
            token_df.to_csv(f"./data/api-scrip-master{'_' + tm}.csv", index=False)
            sleep(5)
            self.master = pd.read_csv(f"./data/api-scrip-master{'_' + tm}.csv")

    def getSymbolToken(self, index, strike, optiontype, expiry):
        df = self.token_df[self.token_df['expiry'] == date(datetime.now().year, datetime.now().month, expiry)]
        df = df[(df['strike'] == (strike*100) & (df['symbol'].str.endswith(optiontype)))]
        return df['token'], df['symbol']

    def updateTrade(self, trd): 
        trd_data = {}
        with open("./data/margin.txt", "r") as fileStore:
            trd_data = fileStore.readline()
            fileStore.close()
        if isinstance(trd_data, str) and trd_data.strip() != "": 
            trd_data = ast.literal_eval(trd_data)
        else: trd_data = {'NIFTY': {'margin': 0, 'trades': []}, 'BANKNIFTY': {'margin': 0, 'trades': []}, 
                          'FINNIFTY': {'margin': 0, 'trades': []}, 'NIFTYMCAP50': {'margin': 0, 'trades': []}, 
                          'SENSEX': {'margin': 0, 'trades': []}, 'BANKEX': {'margin': 0, 'trades': []}}
        
        trades = trd_data[trd.index]['trades']
        if trades:
            for t in trades:
                if t['trade_id'] == trd.trade_id:
                    trades.remove(t)
                    trades.append(trd.to_dict_obj())
                    #  trd_data[trd.index]['trades'][str(trd.trade_id)] = trd.to_dict_obj()
                    break
        else: trd_data[trd.index]['trades'].append(trd.to_dict_obj())
        try:
            with open("./data/margin.txt", "w") as fileStore:
                fileStore.write(str(trd_data))
                fileStore.close()
        except Exception:
            print(traceback.format_exc())
            logger.error(f"trade book, updateTrade {traceback.format_exc()}")

    def getDate(self):
        return datetime.now().strftime("%d/%m/%Y")
    def getTime(self):
        return datetime.now().strftime("%H:%M:%S")
    def getDateTime(self):
        return datetime.now().strftime("%d/%m/%Y, %H:%M:%S %p")
    def dictToDataFrame(self):
        return datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
    
    def securityId(self, index, strike, option, exp_num=1):
        df = self.master
        exp = expiry[index][exp_num - 1]
        df = df[(df['INDEX'] == index) & (df['SEM_OPTION_TYPE'] == option) & 
            (df['SEM_STRIKE_PRICE'] == strike) & (df['SEM_EXPIRY_DATE'] == exp)]
        # print(df)
        return df['SEM_SMST_SECURITY_ID'].values[0] if len(df) == 1 else -1

if __name__ == "__main__":
    print("Utils Processing")
    ut = Utils()
    sid = ut.securityId('BANKNIFTY', '49200', 'CE', 1)
    print(sid)
    #     strike = ScripCode["SEM_SMST_SECURITY_ID"]
    # print("ScripCode: ", strike)
    # exit()