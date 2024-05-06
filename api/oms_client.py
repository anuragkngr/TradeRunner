from position import Position
from utils import Utils
from time import sleep
import traceback, json, logging, os
from datetime import datetime, time, timedelta
conf = json.load(open("./data/configuration.json"))
from time import sleep
from dhanhq import dhanhq
trade_headers=['SYMBOL', 'QUANTITY', 'COST', 'PRICE', 'P&L', 'REALIZED', 'UNREALIZED']
idx_list = {'NIFTY': '13', 'BANKNIFTY': '25', 'FINNIFTY': '27', 'INDIA VIX': '21', 'NIFTYMCAP50': '20', 'BANKEX': '69', 'SENSEX': '51'}
util = Utils()
token_list = [{"exchangeType": 1, "tokens": ["26009"]}]
now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
os.makedirs(f"./logs/{tm}", exist_ok=True)
os.makedirs(f"./data/", exist_ok=True)
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/oms_client.log",
    filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
class OMS_Client(): 
    def __init__(self):
        self.dhan = dhanhq(conf['dhan_id'], conf['dhan_token'])

    def refreshConnection(self, method):
        sleep(5)
        flag = True; cnt = 0;
        while flag:
            cnt += 1;
            print('Refresh Connection ' + method + ': ', cnt)
            result = self.getConnection()
            if result: flag = False
        return result

    def getConnection(self):
        try:
            self.dhan = dhanhq(conf['dhan_id'], conf['dhan_token'])
            return True 
        except Exception: return False

    def positions(self):
        res = {}; pos = []
        try:
            if conf['mock']: res = json.load(open('./data/positions.json'))
            else : res = self.dhan.get_positions()
            logger.info(f"OMS API position response: {json.dumps(res)}")
        except Exception:
            logger.info(f"OMS API  Exception positions response: {traceback.format_exc()}")
            self.refreshConnection('positions')
            # res = self.dhan.get_positions()
        for po in res['data'] :
            if po["positionType"] not in ['CLOSED']:
                pos.append(Position(po))
        return [] if not pos else pos
    
    def getFundLimits(self):
        try:
            if conf['mock']: rms = json.load(open('./data/rms.json'))['data']
            else : rms = self.dhan.get_fund_limits()['data']
            rms = self.dhan.get_fund_limits()['data']
            logger.info(f"OMS API getFundLimits response: {json.dumps(rms)}")
        except Exception:
            logger.info(f"OMS API  Exception getFundLimits response: {traceback.format_exc()}")
            self.refreshConnection('getFundLimits')
            # rms = self.dhan.rmsLimit()['data']
        return {} if rms is None else rms
    
    def print(self) -> dict:
        pos = self.positions();resp = []
        for po in pos:
            tmppo = {
            "SYMBOL": po.symbol,
            "POSITION": po.position,
            "QUANTITY": self.quantity,
            "PRICE": po.price,
            "COST": po.cost_price,
            "P&L": po.pnl,
            "REALISED": po.realised,
            # "UNREALISED": po.unrealised,
            }
            resp.append(tmppo)
        logger.info(f"OMS API print response: {str(resp)}")
        return resp
    
    def placeOrder(self, position, transaction_type) -> bool:
        logger.info(str(position))
        try:
            res = self.dhan.place_order(
            security_id = str(position.security_id), 
            exchange_segment = self.dhan.NSE_FNO,
            transaction_type = transaction_type,
            quantity = abs(int(position.quantity)),
            order_type = self.dhan.MARKET,
            product_type = position.product_type,
            price = 0
            )
            logger.info(f"OMS API execOrder response: {str(res)}")
            sleep(0.4)
            return True
        except Exception:
            logger.info(f"OMS API  Exception placeOrder response: {traceback.format_exc()}")
            return False
             
    def execOrder(self, position, transaction_type) -> bool:
        try:
            # res = 'OK'
            res = self.placeOrder(position, transaction_type)
        except Exception:
            try:
                self.refreshConnection('execOrder')
                res = self.placeOrder(position, transaction_type)
            except Exception:
                logger.info(f"OMS API  Exception execOrder response: {traceback.format_exc()}")
        return res
    def spotStrike(self, index):
        slab = 100 if index == "BANKNIFTY" else 50
        try:
            spot = self.price(index, True)
        except Exception:
            logger.info(f"Positions API  Exception rmsLimit response: {traceback.format_exc()}")
            self.refreshConnection('spotStrike')
        spot = float(spot['close']) if 'close' in spot else -1
        strike = round(spot / slab) * slab
        return strike
    
    def price(self, security, isIndex=False, price=False):
        security_id = security
        if isIndex: 
            security_id = idx_list[security]
            exchange_segment = 'IDX_I'
        else: exchange_segment = 'NSE_FNO'
        try:
            res = self.dhan.intraday_minute_data(
            security_id=security_id, exchange_segment=exchange_segment, instrument_type='OPTIDX')
        except Exception:
            logger.info(f"OMS API  Exception price response: {traceback.format_exc()}")
            self.refreshConnection('price')
            res = {'data': {'open': [12.10], 'high': [12.45], 'low': [12.02], 'close': [12.21]}}
            # res = self.dhan.intraday_minute_data(
            # security_id=security_id, exchange_segment=exchange_segment, instrument_type='OPTIDX')
            return res['data'] 
        
        if price: return res['data']

        res = res['data']
        if res == '': 
            res = {'open': [12.10], 'high': [12.45], 'low': [12.02], 'close': [12.21]}
        res = {'open': res['open'][0], 'high': max(res['high']), 
               'low': min(res['low']), 'close': res['close'][-1]}
        return res

    def CloseAllPositions(self, index=None):
        logger.info(f"OMS Client: CloseAllPositions Starting...")
        pos = self.positions()
        pos = [po for po in pos if index is None or po.index == index]
        self.ClosePositions(pos)
        logger.info(f"OMS Client: CloseAllPositions Completed...")
    
    def ClosePositions(self, positions):
        logger.info(f"OMS Client: ClosePositions Starting...")
        for po in positions:
            try:
                transaction_type = 'BUY' if po.position_type == 'SHORT' else 'SELL'
                self.execOrder(po, transaction_type)
            except Exception:
                logger.info(f"OMS Client: ClosePositions ex {traceback.format_exc()}")
        logger.info(f"OMS Client: ClosePositions Completed...")
        sleep(2)

    def openPositions(self, positions):
        logger.info(f"OMS Client: openPositions Starting...")
        for po in positions:
            try:
                security_id = util.securityId(po.index, int(po.strike_price), po.option_type, 1)
                po.security_id = security_id
                transaction_type = 'SELL' if po.position_type == 'SHORT' else 'BUY'
                self.execOrder(po, transaction_type)
            except Exception:
                logger.info(f"OMS Client: OpenPositions ex {traceback.format_exc()}")
        logger.info(f"OMS Client: openPositions Completed...")
        sleep(2)
    
if __name__ == "__main__": 

    # index = 'NIFTY'
    index = 'BANKNIFTY'
    orders = [
        Position({'index': index, 'drvStrikePrice': 49900, 'drvOptionType': 'CE', 'positionType': 'LONG', 'netQty':  '90'}),
        Position({'index': index, 'drvStrikePrice': 49400, 'drvOptionType': 'PE', 'positionType': 'LONG', 'netQty':  '90'}),
        
        Position({'index': index, 'drvStrikePrice': 49500, 'drvOptionType': 'CE', 'positionType': 'SHORT', 'netQty': '90'}),
        # Position({'index': index, 'drvStrikePrice': 22400, 'drvOptionType': 'PE', 'positionType': 'LONG', 'netQty':  '50'}),
        # Position({'index': index, 'drvStrikePrice': 22800, 'drvOptionType': 'PE', 'positionType': 'SHORT', 'netQty': '50'})
    ]

    oms = OMS_Client()
    # res = oms.price('43694', False, True)
    # res = oms.price(index, True)
    # print(res)
    
    oms.openPositions(orders)
    # exit(0)
    # oms.ClosePositions(orders)
    # oms.CloseAllPositions()
    # oms.CloseAllPositions(index)
    
    
    

