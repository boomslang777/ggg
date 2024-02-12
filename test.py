import SmartApi
import pyotp
import datetime
import pandas as pd
import time
import json
api_key = 'sZCYrTuL'
clientId = 'V53681130'
pwd = '1541'
smartApi = SmartApi.SmartConnect(api_key)
token = "ATG3TC54RUUW7BVKLYEC4VQSLM"
totp=pyotp.TOTP(token).now()
correlation_id = "abc123"
mult = 15
from logzero import logger
data = smartApi.generateSession(clientId, pwd, totp)
authToken = data['data']['jwtToken']
refreshToken = data['data']['refreshToken']

# fetch the feedtoken
feedToken = smartApi.getfeedToken()

# fetch User Profile
res = smartApi.getProfile(refreshToken)
smartApi.generateToken(refreshToken)
res=res['data']['exchanges']

def get_token(instrument_id):
    df = pd.read_csv('OpenAPIScripMaster.csv',low_memory=False)
    row = df[df['symbol'] == instrument_id]

    if not row.empty:
        token = row.iloc[0]['token']
        return token
    else:
        return None

def place_order(instrument_id, token, direction, exc, type, qty,o_type,trigger_price,trade_trigger):
    try:
            orderparams = {
                "variety": "STOPLOSS",
                "tradingsymbol": instrument_id,
                "symboltoken": token,
                "transactiontype": direction,
                "exchange": exc,
                "ordertype": o_type,
                "producttype": type,
                "duration": "DAY",
                "triggerprice": trigger_price,
                "price": trade_trigger,
                "squareoff": "0",
                "stoploss": "0",
                "quantity": qty
            }
            orderId = smartApi.placeOrder(orderparams)
            print("The order id is: {}".format(orderId))
            return orderId
    except Exception as e:
        print("Order placement failed: {}".format(str(e)))   

def get_current_wednesday():
  current_date = datetime.date.today()
  # Check if today is already Wednesday
  if current_date.weekday() == 2:
    return current_date.strftime("%d%b%y").upper()
  # Otherwise, calculate the number of days to add to get to Wednesday
  else:
    days_to_add = (2 - current_date.weekday() + 7) % 7
    wednesday_date = current_date + datetime.timedelta(days=days_to_add)
    return wednesday_date.strftime("%d%b%y").upper()

# strike = input("enter strike")
expiry = get_current_wednesday()
# quantity = input("Enter quantity")
# trigger = int(input("Enter trigger price"))
# right = input("Enter C for Calls or P for puts").upper()
strike = "45000"
trigger = 855.5
right = "C"
quantity = "15"
if right == "C":
    right = "CE"
else :
    right = "PE"    
id = f"BANKNIFTY{expiry}{strike}{right}"
tko = get_token(id)
trade_trigger = str(trigger+0.5)

entry_oid = place_order(id,tko,"BUY","NFO","INTRADAY",quantity,"STOPLOSS_LIMIT",trigger,trade_trigger)
print(f"{entry_oid} is entry order ID")
global order_placed
order_placed = False

def on_message(wsapp, message):
    global order_placed
    client.close_connection()
    if not message or message == b'\x00':
        # Skip processing if the message is empty or a null byte
        return

    try:
        order_data = json.loads(message)

        # Access the order ID and order status directly
        order_id = order_data['orderData']['orderid']
        order_status = order_data['orderData']['orderstatus']

        # Print the results
        logger.info("Order ID: {}".format(order_id))
        logger.info("Order Status: {}".format(order_status))

        if order_status == "AB05" and entry_oid == order_id:
            logger.info("Order executed")
            # Set the flag to indicate that the order has been placed
            order_placed = True
            # Disconnect the client after order execution
            wsapp.close()
            client.close_connection()
    except json.JSONDecodeError:
        logger.error("Error decoding JSON: %s", message)


from SmartApi.smartWebSocketOrderUpdate import SmartWebSocketOrderUpdate
AUTH_TOKEN = authToken
API_KEY = api_key
CLIENT_CODE = clientId
FEED_TOKEN = feedToken
client = SmartWebSocketOrderUpdate(AUTH_TOKEN, API_KEY, CLIENT_CODE, FEED_TOKEN)
client.on_message = on_message
# client.connect()
sl_order_id = place_order(id,tko,"SELL","NFO","INTRADAY",quantity,"STOPLOSS_LIMIT",trigger-5,trigger-4.5)
def check_if_open(order_id):
    oid = smartApi.individual_order_details(order_id)
    if oid['data']['orderstatus'] == 'completed': 
        return True 
    return False
global sl_flag 
sl_flag = False
global t1_flag
t1_flag = False
def move_sl_to_target(order_id):
    global sl_order_id
    sl_order_id = smartApi.modifyOrder(orderid = order_id,variety="NORMAL",price=trigger+80,triggerprice= trigger+79.5,quantity = quantity//2)


def move_sl_to_entry(order_id):
    global sl_order_id
    sl_order_id = smartApi.modifyOrder(orderid = order_id,variety="NORMAL",price=trigger,triggerprice= trigger+0.5,quantity = quantity//2)


def handle_messages(message):
    # global sl_flag
    # global sl_order_id
    # global t1_flag
    # Parse the incoming message
    # data = json.loads(message)
    
    # # Extract the LTP
    ltp = message

    # # Log the LTP
    # logger.info(f"LTP: {ltp}")

    # Define your parameters
    trigger_price = trigger 
    print(f"{trigger_price} is the trigger") # Replace with your actual trigger price
    sl = trigger_price - 5
    t1 = trigger_price + 20
    t2 = trigger_price + 80
    print(f"{ltp} is ltp")
    print(f"{sl_order_id} is stop loss order id")
    # check_if_open(sl_order_id)
    oid = smartApi.individual_order_details(sl_order_id)
    print(oid)
    # Check the conditions
    if ltp <= sl :
        #sl_flag == False
        print("Enter here")
        # sl_flag = True
        logger.info("Stop Loss triggered")
        # close_connection()
    #     # Add your code here to handle the SL condition
    # elif ltp >= t1 and ltp < t2 and sl_flag == False and t1_flag == False:
    #     logger.info("Target 1 achieved")
    #     move_sl_to_entry(sl_order_id)
    #     #Change the target orders to market price
    #     place_order(id,tko,"SELL","NFO","INTRADAY",quantity//2,"STOPLOSS_LIMIT",trigger+20,trigger+19.5)
    #     t1_flag = True
    #     # Add your code here to handle the T1 condition
    # elif ltp >= t2:
    #     logger.info("Target 2 achieved")
    #     move_sl_to_target(sl_order_id)
    #     # close_connection()
    #     # Add your code here to handle the T2 condition


print(f"{tko} is tko")


#retry_strategy=1 for exponential retry mechanism
# sws = SmartWebSocketV2(AUTH_TOKEN, API_KEY, CLIENT_CODE, FEED_TOKEN,max_retry_attempt=3, retry_strategy=1, retry_delay=10,retry_multiplier=2, retry_duration=30)

# def onn_data(wsapp, message):
#     global sl_flag
#     global sl_order_id
#     global t1_flag
#     # Parse the incoming message
#     data = json.loads(message)

#     # Extract the LTP
#     ltp = data['ltp']

#     # Log the LTP
#     logger.info(f"LTP: {ltp}")

#     # Define your parameters
#     trigger_price = trigger  # Replace with your actual trigger price
#     sl = trigger_price - 5
#     t1 = trigger_price + 20
#     t2 = trigger_price + 80
#     # Check the conditions
#     if ltp <= sl and check_if_open(sl_order_id) and sl_flag == False:
#         sl_flag = True
#         logger.info("Stop Loss triggered")
#         sws.close_connection()
#         # Add your code here to handle the SL condition
#     elif ltp >= t1 and ltp < t2 and sl_flag == False and t1_flag == False:
#         logger.info("Target 1 achieved")
#         move_sl_to_entry(sl_order_id)
#         #Change the target orders to market price
#         place_order(id,tko,"SELL","NFO","INTRADAY",quantity//2,"STOPLOSS_LIMIT",trigger+20,trigger+19.5)
#         t1_flag = True
#         # Add your code here to handle the T1 condition
#     elif ltp >= t2:
#         logger.info("Target 2 achieved")
#         move_sl_to_target(sl_order_id)
#         sws.close_connection()
#         # Add your code here to handle the T2 condition


def on_data(wsapp, message):
    logger.info("Ticks: {}".format(message))
    # global sl_flag
    # global sl_order_id
    # global t1_flag
    # # Parse the incoming message
    LTP = message['last_traded_price']/100


    # # Log the LTP
    # logger.info(f"LTP: {ltp}")
    handle_messages(LTP)

def on_control_message(wsapp, message):
    logger.info(f"Control Message: {message}")

def on_open(wsapp):
    logger.info("on open")
    some_error_condition = False
    if some_error_condition:
        error_message = "Simulated error"
        if hasattr(wsapp, 'on_error'):
            wsapp.on_error("Custom Error Type", error_message)
    else:
        sws.subscribe(correlation_id, mode, token_list)
        # sws.unsubscribe(correlation_id, mode, token_list1)

def on_error(wsapp, error):
    logger.error(error)

def on_close(wsapp):
    logger.info("Close")

def close_connection():
    sws.close_connection()


from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from logzero import logger

AUTH_TOKEN = authToken
API_KEY = api_key
CLIENT_CODE = clientId
FEED_TOKEN = feedToken
correlation_id = "abc123"
action = 1
mode = 1
token_list = [
    {
        "exchangeType": 2,
        "tokens": [tko]
    }
]
#retry_strategy=0 for simple retry mechanism
sws = SmartWebSocketV2(AUTH_TOKEN, API_KEY, CLIENT_CODE, FEED_TOKEN,max_retry_attempt=2, retry_strategy=0, retry_delay=10, retry_duration=30)
# Assign the callbacks.
sws.on_open = on_open
sws.on_data = on_data
sws.on_error = on_error
sws.on_close = on_close
sws.on_control_message = on_control_message

sws.connect()