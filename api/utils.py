import ast, traceback, numpy as np, json, pandas as pd, logging
from tabulate import tabulate, SEPARATING_LINE
conf = json.load(open("./data/configuration.json"))
from datetime import datetime, timedelta, time, date
# from logzero import logger
now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application{'_' + now.strftime("%H-%S")}.log",
    filemode="w", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
import requests
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

    def updateTradeMargin(self, index, margin): 
        trd_data = {}
        with open("./data/margin.txt", "r") as fileStore:
            trd_data = fileStore.readline()
            fileStore.close()
        if isinstance(trd_data, str) and trd_data.strip() != "": 
            trd_data = ast.literal_eval(trd_data)
        else: trd_data = {}
        trd_data[index] = margin
        try:
            with open("./data/margin.txt", "w") as fileStore:
                res = fileStore.write(str(trd_data))
                fileStore.close()
        except Exception:
            print(traceback.format_exc())
            logger.error(f"trade book, saveTrade {traceback.format_exc()}")

    def print(self):  # sourcery skip: extract-duplicate-method
        tradeNotes = []
        notesSummary = []
        for trd in self.trades:
            if trd.status == "open":
                tmp = trd.orders_print()
                df = pd.DataFrame(tmp)
                if not tradeNotes: 
                    tradeNotes = df.values.tolist()
                else: 
                    tradeNotes.append(SEPARATING_LINE)
                    tradeNotes = tradeNotes + df.values.tolist()
                tmp = self.tradeNoteTable(trd)
                df = pd.DataFrame(tmp)
                if not notesSummary: 
                    notesSummary = df.values.tolist()
                else: 
                    notesSummary.append(SEPARATING_LINE)
                    notesSummary = notesSummary + df.values.tolist()
        # dframe = pd.DataFrame(tradeNotes)
        dframe = tabulate(tradeNotes, tablefmt="rounded_outline", floatfmt=".2f")
        logger.info(dframe)
        # print(dframe)
        # dframe = pd.DataFrame(notesSummary)
        dframe = tabulate(notesSummary, tablefmt="mixed_outline", floatfmt=".2f")
        logger.info(dframe)
        # print(dframe)

    def tradeNoteTable(self, trd):
        # print("aaa--trd.index", trd.index, self.broker.getPrice(trd.index, 'IDX'))
        return [
            {
                1: f"Fund: {str(round(trd.margin, 2))}",
                2: f"Spot: {str(round(self.broker.getPrice(trd.index, 'IDX')))}",
                3: f"P&L: {str(round(trd.pnl))} ({str(round(trd.pnlPercent, 2))})",
                4: f"Target: {str(round(trd.reward, 2))}",
                6: f"SL: {str(round(trd.risk, 2))}",
                5: f"Step: {str(round(trd.step, 2))}",
            }
        ]
    
    def tradeNote(self, trd):
        return (
            f"""\n#####   P&L: {str(round(trd.pnl, 2))}, Utilized: {str(round(trd.margin, 2))}, P&L (%): {str(round(trd.pnlPercent, 2))}, SL (%): {str(round(trd.risk, 2))}   #####\n"""
        )
    def notesTable(self):
        loss = 0;profit = 0
        if self.openTrades > 0:
            loss = sum(trd.risk for trd in self.trades if trd.status in ["open"])
            profit = sum(trd.reward for trd in self.trades if trd.status in ["open"])
            return f"""[['Open Trades: {str(self.openTrades)}', 'Total: {str(round(self.utilized, 2))}', 'P&L: {str(round(self.pnl))} ({str(round(self.pnlPercent, 2))})', 'COM-Target: {str(round(profit, 2))}', 'COM-SL: {str(round(loss, 2))}']]"""


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