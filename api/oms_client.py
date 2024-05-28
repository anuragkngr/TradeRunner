from utils import Utils
from position import Position
from order_management_system import OMS
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
util = Utils()
oms = OMS()
now = datetime.now()
tm = now.strftime("%Y") + "-" + now.strftime("%m") + "-" + now.strftime("%d")
logging.basicConfig(
    level=logging.INFO, filename=f"./logs/{tm}/order_application.log",
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
    logger.info(str(position))
    print(f" position: {position.to_dict()}")
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
        logger.info(f"OMS API Client: execOrder response: {str(res)}")
        print(f"OMS API Client: execOrder response: {str(res)}")
        sleep(0.4)
        return True
    except Exception:
        logger.info(f"OMS Client: Exception placeOrder response: {traceback.format_exc()}")
        print(f"OMS Client: Exception placeOrder response: {traceback.format_exc()}")
        return False
            
def execOrder(position, transaction_type) -> bool:
    try:
        # res = 'OK'
        res = placeOrder(position, transaction_type)
    except Exception:
        logger.info(f"OMS Client: Exception execOrder response: {traceback.format_exc()}")
        print(f"OMS Client: Exception execOrder response: {traceback.format_exc()}")
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
    for po in positions:
        try:
            security_id = util.securityId(po.index, int(po.strike_price), po.option_type, 1)
            po.security_id = security_id['s_id']
            po.symbol = security_id['symbol']
            transaction_type = 'SELL' if po.position_type == 'SHORT' else 'BUY'
            res = execOrder(po, transaction_type)
        except Exception:
            logger.info(f"OMS Client: OpenPositions ex {traceback.format_exc()}")
            print(f"OMS Client: OpenPositions ex {traceback.format_exc()}")
    logger.info(f"OMS Client: openPositions Completed...")
    print(f"OMS Client: openPositions Completed...")
    sleep(.2)

def pObj(index, strike, option, position, lots):
    quantity = 25 if index == 'NIFTY' else 15
    quantity = str(quantity * lots)
    position = 'SHORT' if position.upper() == 'S' else 'LONG'
    req = {'index': index, 'drvStrikePrice': strike, 'drvOptionType': 
           option, 'positionType': position, 'netQty':  quantity}
    pos = Position(req, True)
    return pos


    
if __name__ == "__main__": 
    
    index = 'NIFTY'

    slab = 50 if index == 'NIFTY' else 100; lots = 4
    # c_sell = p_sell = c_buy = p_buy = None
    #call duwn, sell CALL
    c_sell = list(open_high_low.find({'index': index, 'open_high': True, 'option_type': 'CALL'}))
    if len(c_sell) > 0: 
        c_sell = sorted(c_sell, key=lambda x: x['strike'])
        print(f'c_sell 1: {c_sell}')
        c_sell = int(c_sell[0]['strike'])
        print(f'c_sell 2: {c_sell}')
    else: c_sell = None
    #put duwn, sell PUT
    p_sell = list(open_high_low.find({'index': index, 'open_high': True, 'option_type': 'PUT'}))
    if len(p_sell) > 0: 
        p_sell = sorted(p_sell, key=lambda x: x['strike'], reverse=True)
        print(f'p_sell 1: {p_sell}')
        p_sell = int(p_sell[0]['strike'])
        print(f'p_sell 2: {p_sell}')
    else: p_sell = None
    #call up, buy CALL
    c_buy = list(open_high_low.find({'index': index, 'open_high': False, 'option_type': 'CALL'}))
    if len(c_buy) > 0: 
        c_buy = sorted(c_buy, key=lambda x: x['strike'])
        print(f'c_buy 1: {c_buy}')
        c_buy = int(c_buy[0]['strike'])
        print(f'c_buy 2: {c_buy}')
    else: c_buy = None
    #put up, buy PUT
    p_buy = list(open_high_low.find({'index': index, 'open_high': False, 'option_type': 'PUT'}))
    if len(p_buy) > 0: 
        p_buy = sorted(p_buy, key=lambda x: x['strike'], reverse=True)
        print(f'p_buy 1: {p_buy}')
        p_buy = int(p_buy[0]['strike'])
        print(f'p_buy 2: {p_buy}')
    else: p_buy = None

    if c_buy is not None:
        orders = [ pObj(index, c_buy, 'CE', 'B', lots) ]
        res = openPositions(orders)

    if p_buy is not None:
        orders = [ pObj(index, p_buy, 'PE', 'B', lots) ]
        res = openPositions(orders)

    if c_sell is not None:
        orders = [ pObj(index, (c_sell + (slab + (8*slab))), 'CE', 'B', lots),
                  pObj(index, c_sell, 'CE', 'S', lots) ]
        res = openPositions(orders)

    if p_sell is not None:
        orders = [ pObj(index, (p_sell + (slab - (8*slab))), 'PE', 'B', lots),
                  pObj(index, p_sell, 'PE', 'S', lots) ]
        res = openPositions(orders)                



    orders = [
        pObj(index, 23250, 'CE', 'S', 4),
        pObj(index, 23350, 'CE', 'S', 4),
    ]

    # res = openPositions(orders)
    # res = closePositions(orders)
    # print(res)
    
    
    # exit(0)
    # ClosePositions(orders)
    # CloseAllPositions()
    # CloseAllPositions(index)
    
    
    

