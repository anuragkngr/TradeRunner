import ast, traceback, json, pandas as pd, logging
conf = json.load(open("./data/configuration.json"))
from datetime import datetime, date
now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application.log",
    filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
flag = False
if flag:
    url = 'https://images.dhan.co/api-data/api-scrip-master.csv'
    token_df = pd.read_csv(url)
    # d = requests.get(url).json()
    # token_df = pd.DataFrame.from_dict(d)
    token_df = token_df[(token_df['SEM_INSTRUMENT_NAME'] == 'OPTIDX') | (token_df['SEM_INSTRUMENT_NAME'] == 'INDEX')]
    token_df['SEM_EXPIRY_DATE'] = pd.to_datetime(token_df['SEM_EXPIRY_DATE'], format = 'mixed').apply(lambda x: x.date())
    token_df.to_csv(f"./data/api-scrip-master{'_' + tm}.csv", index=False)
# else:
    # token_df = pd.read_csv("./data/api-scrip-master.csv")
    # token_df_idx = token_df[(token_df.instrumenttype == 'AMXIDX')].head(200)
class Utils:

    def __init__(self, load=False):
        if load: self.master = pd.read_csv(f"./data/api-scrip-master{'_' + tm}.csv")

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

    def getLTPDict(self) -> dict:
        dic_data = {}
        with open("./data/ltp.txt", "r") as fileStore:
            dic_data = fileStore.readline()
            dic_data = ast.literal_eval(dic_data)
        return dic_data

if __name__ == "__main__":
    print("Utils Processing")
    ut = Utils(True)
    print(ut.master)
    #     strike = ScripCode["SEM_SMST_SECURITY_ID"]
    # print("ScripCode: ", strike)
    # exit()