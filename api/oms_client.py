from utils import Utils
from position import Position
from order_management_system import OMS, idx_list
import traceback, json, logging, warnings, pymongo
from datetime import datetime
conf = json.load(open("./data/configuration.json"))
from time import sleep
from dhanhq import dhanhq
dhan = dhanhq(conf['dhan_id'], conf['dhan_token'])
warnings.filterwarnings('ignore')
client = pymongo.MongoClient(conf['db_url_lcl'])
dblist = client.list_database_names()
mydb = client["tradestore"]
open_high_low = mydb["open_high_low"]
indexes = mydb["indexes"]
util = Utils()
oms = OMS()
order_flag = False
order_sleep=4
now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/oms_client.log", force=True,
    filemode="a", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger()
def positions():
        res = {}; pos = []
        try:
            if conf['mock']: res = json.load(open('./data/positions.json'))
            else : res = dhan.get_positions()
            # res = json.load(open('./data/positions.json'))
            print(f"OMS Client positions count: {len(res['data'])}")
            logger.info(f"OMS Client: Positions: {json.dumps(res)}")
            
        except Exception:
            logger.info(f"OMS Client  Exception positions response: {traceback.format_exc()}")
            print(f"OMS Client  Exception positions response: {traceback.format_exc()}")
        for po in res['data'] :
            if po["positionType"] not in ['CLOSED']:
                pos.append(Position(po))
        return [] if not pos else pos

def placeOrder(position, transaction_type) -> bool:
    logger.info(f"OMS Client: placeOrder Starting...")
    print(f"OMS Client: placeOrder Starting...")
    logger.info(f"OMS API Client: placeOrder request:\n{json.dumps(position.to_dict_order(), indent=4)}")
    print(f"OMS API Client: placeOrder position:\n{json.dumps(position.to_dict_order(), indent=4)}")
    try:
        res = dhan.place_order(
        security_id = str(position.security_id), 
        exchange_segment = dhan.NSE_FNO,
        transaction_type = transaction_type,
        quantity = abs(int(position.quantity)),
        order_type = dhan.MARKET,
        product_type = position.product_type,
        price = 0
        )
        logger.info(f"OMS API Client: placeOrder response: \n{json.dumps(res, indent=4)}")
        print(f"OMS API Client: placeOrder response: \n{json.dumps(res, indent=4)}")
        # print(f"OMS API Client: execOrder response: {str(res)}")
        # sleep(0.2)
        logger.info(f"OMS Client: placeOrder Completed...")
        print(f"OMS Client: placeOrder Completed...")
        return res if res['status'] != 'failure' else None
    except Exception:
        logger.info(f"OMS Client: Exception placeOrder response: {traceback.format_exc()}")
        print(f"OMS Client: Exception placeOrder response: {traceback.format_exc()}")
        return None

def execOrder(position, transaction_type) -> bool:
    logger.info(f"OMS Client: execOrder Starting...")
    print(f"OMS Client: execOrder Starting...")
    try:
        print(f'{transaction_type}: [{position.index}-{position.strike_price}-{position.option_type}-{position.quantity}]')
        res = 'OMS Client: execOrder Order offline'
        if order_flag: res = placeOrder(position, transaction_type)
        print(f'OMS Client: execOrder response = {res}')
    except Exception:
        logger.info(f"OMS Client: Exception execOrder response: {traceback.format_exc()}")
        print(f"OMS Client: Exception execOrder response: {traceback.format_exc()}")
    logger.info(f"OMS Client: execOrder Completed...")
    print(f"OMS Client: execOrder Completed...")
    return res

def closeAllPositions(index=None):
    logger.info(f"OMS Client: CloseAllPositions Starting...")
    print(f"OMS Client: CloseAllPositions Starting...")
    pos = positions()
    pos = [po for po in pos if index is None or po.index == index]
    closePositions(pos)
    logger.info(f"OMS Client: CloseAllPositions Completed...")
    print(f"OMS Client: CloseAllPositions Completed...")

def closePositions(positions):
    logger.info(f"OMS Client: ClosePositions Starting...")
    print(f"OMS Client: ClosePositions Starting...")
    for po in positions:
        try:
            transaction_type = 'BUY' if po.position_type == 'SHORT' else 'SELL'
            res = execOrder(po, transaction_type)
        except Exception:
            logger.info(f"OMS Client: ClosePositions ex {traceback.format_exc()}")
            print(f"OMS Client: ClosePositions ex {traceback.format_exc()}")
    logger.info(f"OMS Client: ClosePositions Completed...")
    print(f"OMS Client: ClosePositions Completed...")
    sleep(.2)

def openPositions(positions):
    logger.info(f"OMS Client: openPositions Starting...")
    print(f"OMS Client: openPositions Starting...")
    # pos = [po.to_dict() for po in positions]
    pos_print = [po.to_dict_order() for po in positions]
    logger.info(f"OMS Client: openPositions positions=\n{json.dumps(pos_print, indent=4)}")
    print(f"OMS Client: openPositions positions=\n{json.dumps(pos_print, indent=4)}")
    for po in positions:
        try:
            security_id = util.securityId(po.index, int(po.strike_price), po.option_type, 1)
            po.security_id = security_id['s_id']
            po.symbol = security_id['symbol']
            transaction_type = 'SELL' if po.position_type == 'SHORT' else 'BUY'
            res = execOrder(po, transaction_type)
            if order_flag and res is None:
                logger.info(f"OMS Client: openPositions execOrder failed. Stop the execution")
                print(f"\nOMS Client: openPositions execOrder failed. Stop the execution")

        except Exception:
            logger.info(f"OMS Client: OpenPositions ex {traceback.format_exc()}")
            print(f"OMS Client: OpenPositions ex {traceback.format_exc()}")
    logger.info(f"OMS Client: openPositions Completed...")
    print(f"OMS Client: openPositions Completed...")
    # sleep(10)

def pObj(index, strike, option, position, lots):
    quantity = 25 if index == 'NIFTY' else 15
    quantity = str(quantity * lots)
    position = 'SHORT' if position.upper() == 'S' else 'LONG'
    req = {'index': index, 'drvStrikePrice': strike, 'drvOptionType': 
           option, 'positionType': position, 'netQty':  quantity}
    pos = Position(req, True)
    return pos

if __name__ == "__main__": 
    # index = 'NIFTY'
    index = 'BANKNIFTY'
    # idx = indexes.find_one({'security_id': int(idx_list[index])}, sort=[('LTT', -1)])
    spot = oms.spotStrike(index)

    slab = 50 if index == 'NIFTY' else 100
    lots = 4; hedge_strike_gap=4
    stb_str = slab*2 if index == 'NIFTY' else slab*5
    # c_sell = p_sell = c_buy = p_buy = None
    #call duwn, sell CALL
    c_sell = open_high_low.find_one({'index': index, 'open_high': True, 'option_type': 'CALL', 'strike': {'$lte': spot}}, sort=[('strike', -1)])
    if c_sell is None: c_sell = open_high_low.find_one({'index': index, 'open_high': True, 'option_type': 'CALL', 'strike': {'$gte': spot}}, sort=[('strike', 1)])
    if c_sell is not None: 
        c_sell = sorted([c_sell], key=lambda x: x['strike'])
        c_sell = int(c_sell[0]['strike'])
    else: c_sell = None
    #put duwn, sell PUT
    p_sell = open_high_low.find_one({'index': index, 'open_high': True, 'option_type': 'PUT', 'strike': {'$gte': spot}}, sort=[('strike', 1)])
    if p_sell is None: p_sell = open_high_low.find_one({'index': index, 'open_high': True, 'option_type': 'PUT', 'strike': {'$lte': spot}}, sort=[('strike', -1)])
    if p_sell is not None: 
        p_sell = sorted([p_sell], key=lambda x: x['strike'], reverse=True)
        p_sell = int(p_sell[0]['strike'])
    else: p_sell = None
    #call up, buy CALL
    c_buy = open_high_low.find_one({ 'index': index, 'open_high': False, 'option_type': 'CALL', 'strike': {'$lte': spot}}, sort=[('strike', -1)])
    if c_buy is None: c_buy = open_high_low.find_one({ 'index': index, 'open_high': False, 'option_type': 'CALL', 'strike': {'$gte': spot}}, sort=[('strike', 1)])
    if c_buy is not None: 
        c_buy = sorted([c_buy], key=lambda x: x['strike'])
        c_buy = int(c_buy[0]['strike'])
    else: c_buy = None
    #put up, buy PUT
    p_buy = open_high_low.find_one({'index': index, 'open_high': False, 'option_type': 'PUT', 'strike': {'$gte': spot}}, sort=[('strike', 1)])
    if p_buy is None: p_buy = open_high_low.find_one({'index': index, 'open_high': False, 'option_type': 'PUT', 'strike': {'$lte': spot}}, sort=[('strike', -1)])
    if p_buy is not None: 
        p_buy = sorted([p_buy], key=lambda x: x['strike'], reverse=True)
        p_buy = int(p_buy[0]['strike'])
    else: p_buy = None

    order_flag = True
    lots = 4; order_sleep = 4

    if c_buy is not None:
        orders = [ pObj(index, c_buy, 'CE', 'B', lots*2) ]
        res = openPositions(orders)
        if order_flag: sleep(order_sleep)

    # order_flag = False; lots = 4

    if p_buy is not None:
        orders = [ pObj(index, p_buy, 'PE', 'B', lots*2) ]
        res = openPositions(orders)
        if order_flag: sleep(order_sleep)
    # order_flag = True; lots = 4

    if c_sell is not None:
        spot_strike = c_sell + (hedge_strike_gap*slab)
        spot_strike = round(spot_strike / stb_str) * stb_str

        orders = [ pObj(index, spot_strike, 'CE', 'B', lots),
                  pObj(index, c_sell, 'CE', 'S', lots) ]
        res = openPositions(orders)
        if order_flag: sleep(order_sleep)

    # order_flag = True; lots = 4

    if p_sell is not None:
        spot_strike = p_sell - (hedge_strike_gap*slab)
        spot_strike = round(spot_strike / stb_str) * stb_str

        orders = [ pObj(index, spot_strike, 'PE', 'B', lots),
                  pObj(index, p_sell, 'PE', 'S', lots) ]
        res = openPositions(orders)                

    # orders = [
    #     pObj(index, 23250, 'CE', 'S', 4),
    #     pObj(index, 23350, 'CE', 'S', 4),
    # ]

    # res = openPositions(orders)
    # res = closePositions(orders)
    # print(res)
    
    
    # exit(0)
    # ClosePositions(orders)
    # CloseAllPositions()
    # CloseAllPositions(index)
    
    
    

