from position import Position
from utils import Utils
import traceback, json, logging, pandas_ta as ta, warnings, pandas as pd
from datetime import datetime
conf = json.load(open("./data/configuration.json"))
from time import sleep
from dhanhq import dhanhq
warnings.filterwarnings('ignore')
trade_headers=['SYMBOL', 'QUANTITY', 'COST', 'PRICE', 'P&L', 'REALIZED', 'UNREALIZED', 'OI', 'OI_BUY', 'OI_SEL']
trade_columns=['STRATEGY', 'P&L', 'SL', 'TARGET', 'SWING']
idx_list = {'NIFTY': '13', 'BANKNIFTY': '25', 'FINNIFTY': '27', 'INDIA VIX': '21', 'NIFTYMCAP50': '20', 'BANKEX': '69', 'SENSEX': '51'}
fut_list = {'NIFTY': '46930', 'BANKNIFTY': '46923'}
util = Utils()
token_list = [{"exchangeType": 1, "tokens": ["26009"]}]
now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/application.log",
    filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
class OMS(): 
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

    def getIndicators(self, index, intShort=None, intLong=None):
        try:
            response = {}
            res = self.price(fut_list[index], False, True, 'FUTIDX')
            # if conf['mock']: res = json.load(open(f'./logs/{tm}/market_feed.json'))
            # else : res = self.dhan.get_order_list()
            # res = json.load(open(f'./logs/{tm}/market_feed.json'))
            if intShort is None:
                intShort = len(res['close']) - 1
            if intLong is None:
                intLong = int(intShort/2)
            # temp = self.getIndicator(res, index, 'vwap', intShort)
            # response['vwap'] = temp
            temp = self.getIndicator(res, index, 'sma', intShort, intLong)
            response['sma'] = temp
            temp = self.getIndicator(res, index, 'ema', intShort, intLong)
            response['ema'] = temp
            return response
        except Exception: return None

    def getIndicator(self, chart, index, indicator='vwap', interval=None, cross=None):
        try:
            df = pd.DataFrame(chart)
            tmp_list = []
            for i in df["start_Time"]:
                tmp = self.dhan.convert_to_date_time(i)
                tmp_list.append(tmp)
            df['date'] = tmp_list
            df.set_index('date', inplace=True)
            if interval is None:
                interval = len(df.close) - 1
            if cross is None:
                cross = int(interval/2)
            if indicator == 'vwap':
                df['indicator'] = ta.vwap(df.high, df.low, df.close, df.volume)
            if indicator == 'sma':
                df['indicator'] = ta.sma(df.close, interval)
                if cross > 0:
                    df['indicator_2'] = ta.sma(df.close, cross)
            if indicator == 'ema':
                df['indicator'] = ta.ema(df.close, interval)
                if cross > 0:
                    df['indicator_2'] = ta.ema(df.close, cross)
            df.reset_index(inplace=True)
            # df['ema'] = ta.ema(df.close, 10, min_periods=1)
            # df['a_vwap'] = ta.vwap(df.high, df.low, df.close, df.volume, anchor='D')
            
            if cross == 0: response = {'indicator': list(df.indicator)[-1]}
            elif indicator in ['sma', 'ema']:
                df['ind_1_above_2'] = (df["indicator"] >= df["indicator_2"]).astype(int)
                df['ind_1_cross_2'] = df['ind_1_above_2'].diff().astype('Int64')
                response = {'index': index, 'name': indicator, 'indicator': list(df.indicator)[-1], 
                        'indicator_2': list(df.indicator_2)[-1], 'ind_1_cross_2': list(df.ind_1_cross_2)[-1]}
            # if indicator in ['sma']:
            #     print(list(df.ind_1_cross_2))
            return response
        except Exception: return None


    def positions(self):
        sleep(1)
        res = {}; pos = []
        try:
            if conf['mock']: res = json.load(open('./data/positions.json'))
            else : res = self.dhan.get_positions()
            # res = json.load(open('./data/positions.json'))
            logger.info(f"OMS API position response: {json.dumps(res)}")
        except Exception:
            logger.info(f"OMS API  Exception positions response: {traceback.format_exc()}")
            self.refreshConnection('positions')
            # res = self.dhan.get_positions()
        for po in res['data'] :
            if po["positionType"] not in ['CLOSED'] and po['securityId'] not in ['55116', '71302']:
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
    
    def getOrderBook(self):
        if conf['mock']: res = json.load(open('./data/order_book.json'))
        else : res = self.dhan.get_order_list()
        # res = json.load(open('./data/order_book.json'))
        logger.info(f"OMS API getOrderBook response: {json.dumps(res)}")
        return None if res is None or res['data'] is None or res['data'] == '' else res['data']

    def updateCostPrice(self, positions):
        sleep(1)
        res = self.getOrderBook()
        for pos in positions:
            self.updatePositionCostPrice(res, pos)
        return positions
    
    def updatePositionCostPrice(self, res, pos):
        for po in res:
            transactionType = 'SHORT' if po['transactionType'] == 'SELL' else 'LONG'
            if po['securityId'] == pos.security_id and pos.position_type == transactionType and pos.option_type == po['drvOptionType']:
                pos.cost_price = po['price']
                break
            # order = sorted(order, key=lambda x: datetime.strptime(x['exchtime'], '%d-%b-%Y %H:%M:%S'))
            # book_price = order[-1]['averageprice']
    
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
        try:
            res = self.dhan.place_order(
            security_id = position.security_id, 
            exchange_segment = self.dhan.NSE_FNO,
            transaction_type = transaction_type,
            quantity = abs(int(position.quantity)),
            order_type = self.dhan.MARKET,
            product_type = position.product_type,
            price = 0
            )
            logger.info(f"OMS API execOrder response: {str(res)}")
            print(res)
            return True
        except Exception:
            logger.info(f"OMS API  Exception placeOrder response: {traceback.format_exc()}")
            return False
             
    def execOrder(self, position, transaction_type) -> bool:
        order_online = conf['order_online']
        try:
            if not order_online: res = False
            else: res = self.placeOrder(position, transaction_type)
            # print('sample request: ', position)
            # sleep(1)
        except Exception:
            try:
                self.refreshConnection('execOrder')
                res = self.placeOrder(position, transaction_type)
            except Exception:
                logger.info(f"OMS API  Exception execOrder response: {traceback.format_exc()}")
        return res

    def matchOrder(self, index, position, m_price, direction):
        slab = 100 if index == "BANKNIFTY" else 50
        strike = position.strikeprice; di = 1000;final_stike;final_scripCode;tradingSymbol=''
        for idx in range(3):
            strike = (strike + (slab*(idx + 1))) if direction == "UP" else (strike - (slab*(idx + 1)))
            scripCode, symbol = util.getSymbolToken(index, strike, position.optiontype, position.expirydate)
            n_price = self.optionPrice(scripCode)
            dif = abs(n_price - m_price)
            if dif < di: 
                di = dif
                final_stike = strike
                final_scripCode = scripCode
                tradingSymbol = symbol
            else: 
                position.strikeprice = float(final_stike)
                position.symboltoken = final_scripCode
                position.tradingSymbol = tradingSymbol
                position.netprice = position.avgnetprice = position.ltp = n_price
        return position, 

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
    
    def price(self, security, isIndex=False, price=False, instrument_type='OPTIDX'):
        security_id = security; res = None
        if isIndex: 
            security_id = idx_list[security]
            exchange_segment = 'IDX_I'
        else: exchange_segment = 'NSE_FNO'
        try:
            
            res = self.dhan.intraday_minute_data(
            security_id=security_id, exchange_segment=exchange_segment, instrument_type=instrument_type)
            logger.info(f"OMS API price price response: {json.dumps(res)}")
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
            res = {'open': [-1], 'high': [-1], 'low': [-1], 'close': [-1]}
        res = {'open': res['open'][0], 'high': max(res['high']), 
               'low': min(res['low']), 'close': res['close'][-1]}
        return res
 
    def closeAllTrade(self, book):
        for trd in book.trades: self.closeTrade(trd)

    def closeTrade(self, trade):
        flag = True
        for pos in trade.positions:
            if pos.position_type == 'SHORT':
                res = self.execOrder(pos, "BUY")
                if not res:
                    flag = False
                    break
        if flag:
            sleep(1)
            for pos in trade.positions:
                if pos.position_type == 'LONG':
                    res = self.execOrder(pos, "SELL")
                    logger.info(res)
                    if not res:
                        flag = False
                        break
        return flag
    
if __name__ == "__main__": 
    tradingsymbol = 'NIFTY'  
    oms = OMS()
    res = oms.price('BANKNIFTY', True, True)
    # res = []
    # res = oms.getIndicators('BANKNIFTY')
    print(res)
    # res = oms.price('BANKNIFTY', True)
    # pos = pos['data']
    # for po in pos:
        # if po['positionType'] != 'CLOSED': res.append(po)
    # print((json.dumps(res)))
    
    

