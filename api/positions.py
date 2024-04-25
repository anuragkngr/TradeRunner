# # import sys
# # sys.path.append("../TradeRunner")
# # from api.startup import *
# import json
# from position import Position
# conf = json.load(open("./data/configuration.json"))
# # from api.order import Order
# class Positions:
#     def __init__(self, pos):
#         self.positions = [Position(po) for po in pos if po["NetQty"] > 0]

#     def to_dict(self):
#         return [po.to_dict() for po in self.positions]
    
# if __name__ == "__main__": 
#     # pos = dhan.get_order_by_id("52240313721046")
#     # pos = dhan.get_order_list()
#     print("pos")
#     # pos = json.load(open('./data/positions.json'))['data']
#     # poss = Positions(pos)
#     # for x in poss.positions:
#         # print(x.ScripName.split('-')[0])
#     # p1 = [x for x in poss.positions if x.ScripName.split('-')[0] == "FINNIFTY"]
#     # p2 = [x for x in poss.positions if x.ScripName.split('-')[0] == "NIFTY"]
#     # p2 = [x for x in poss.positions if x.ScripName.split('-')[0] == "NIFTY"]
#     # print("p1 = ", poss.to_dict())
#     # print("p1 = ", type(poss.positions))
#     # print("p1 = ", len(poss.positions))
#     # for p in poss.positions:
#     #     print("aaa")
#     #     print("p11 = ", type(p))
#     #     print("p12 = ", p)
#     # print("p2 = ", p2)
#     # trade = Trade(pos.positions)
#     # print(trade.order_print())
#     # print(pos)
#     # pos.to_print() <class 'dict'>
#     # print(json.dumps(pos.to_dict()))