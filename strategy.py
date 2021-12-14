import ccxt, config
import pandas as pd
from ta.trend import EMAIndicator
import winsound
from smtplib import SMTP

duration = 1000  # milliseconds
freq = 440  # Hz

symbolName = input("Symbol Name (BTC, ETH, LTC...): ").upper()
leverage = input ("Leverage: ")
islemeGirecekPara = input("What percentage of the total money will you trade? (25, 50, 100...): ")
zamanAraligi = input("Time interval (1m,3m,5m,15m,30m,45m,1h,2h,4h,6h,8h,12h,1d): ").lower()
symbol = str(symbolName) + "/USDT"
slowEMAValue = input ("Slow Ema Value: ")
fastEMAValue = input ("Fast Ema Value: ")
stopLoss = input("StopLoss %: ")
tp1 = input("TakeProfit 1 %: ")
tp2 = input("TakeProfit 2 %: ")

alinacak_miktar = 0

kesisim = False
longPozisyonda = False
shortPozisyonda = False
pozisyondami = False
takeprofit1 = False
takeprofit2 = False

# API CONNECT
exchange = ccxt.binance({
"apiKey": config.apiKey,
"secret": config.secretKey,

'options': {
'defaultType': 'future'
},
'enableRateLimit': True
})

while True:
    try:
        
        balance = exchange.fetch_balance()
        free_balance = exchange.fetch_free_balance()
        positions = balance['info']['positions']
        newSymbol = symbolName+"USDT"
        current_positions = [position for position in positions if float(position['positionAmt']) != 0 and position['symbol'] == newSymbol]
        position_bilgi = pd.DataFrame(current_positions, columns=["symbol", "entryPrice", "unrealizedProfit", "isolatedWallet", "positionAmt", "positionSide"])
        
        #Pozisyonda olup olmadığını kontrol etme
        if not position_bilgi.empty and position_bilgi["positionAmt"][len(position_bilgi.index) - 1] != 0:
            pozisyondami = True
        else: 
            pozisyondami = False
    
            shortPozisyonda = False
            longPozisyonda = False
            
        
        # Long pozisyonda mı?
        if pozisyondami and float(position_bilgi["positionAmt"][len(position_bilgi.index) - 1]) > 0:
            longPozisyonda = True
            shortPozisyonda = False
        # Short pozisyonda mı?
        if pozisyondami and float(position_bilgi["positionAmt"][len(position_bilgi.index) - 1]) < 0:
            shortPozisyonda = True
            longPozisyonda = False
        
        
        # LOAD BARS
        bars = exchange.fetch_ohlcv(symbol, timeframe=zamanAraligi, since = None, limit = 1500)
        df = pd.DataFrame(bars, columns=["timestamp", "open", "high", "low", "close", "volume"])

        # LOAD SLOW EMA
        slowEma= EMAIndicator(df["close"], float(slowEMAValue))
        df["Slow Ema"] = slowEma.ema_indicator()
        
        # LOAD FAST EMA
        FastEma= EMAIndicator(df["close"], float(fastEMAValue))
        df["Fast Ema"] = FastEma.ema_indicator()
        
        if (df["Fast Ema"][len(df.index)-3] < df["Slow Ema"][len(df.index)-3] and df["Fast Ema"][len(df.index)-2] > df["Slow Ema"][len(df.index)-2]) or (df["Fast Ema"][len(df.index)-3] > df["Slow Ema"][len(df.index)-3] and df["Fast Ema"][len(df.index)-2] < df["Slow Ema"][len(df.index)-2]):
            kesisim = True
        else: 
            kesisim = False
            
        # LONG ENTER
        def longEnter(alinacak_miktar):
            order = exchange.create_market_buy_order(symbol, alinacak_miktar)
            winsound.Beep(freq, duration)
            
        # LONG EXIT
        def longExit(satilacak_miktar):
            order = exchange.create_market_sell_order(symbol, satilacak_miktar, {"reduceOnly": True})
            winsound.Beep(freq, duration)

        # SHORT ENTER
        def shortEnter(alinacak_miktar):
            order = exchange.create_market_sell_order(symbol, alinacak_miktar)
            winsound.Beep(freq, duration)
            
        # SHORT EXIT
        def shortExit(satilacak_miktar):
            order = exchange.create_market_buy_order(symbol, (satilacak_miktar * -1), {"reduceOnly": True})
            winsound.Beep(freq, duration)
        
        # BULL EVENT
        if kesisim and df["Fast Ema"][len(df.index)-1] > df["Slow Ema"][len(df.index)-1] and longPozisyonda == False:
            if shortPozisyonda:
                print("SHORT İŞLEMDEN ÇIKILIYOR...")
                satilacakMiktar = float(position_bilgi["positionAmt"][len(position_bilgi.index) - 1])
                shortExit(satilacakMiktar)
            alinacak_miktar = (((float(free_balance["USDT"]) / 100 ) * float(islemeGirecekPara)) * float(leverage)) / float(df["close"][len(df.index) - 1])
            print("LONG İŞLEME GİRİLİYOR...")
            longEnter(alinacak_miktar)
            takeprofit1 = False
            takeprofit1 = False
            baslik = symbol
            message = "LONG ENTER\n" + "Toplam Para: " + str(balance['total']["USDT"])
            content = f"Subject: {baslik}\n\n{message}"
            mail = SMTP("smtp.gmail.com", 587)
            mail.ehlo()
            mail.starttls()
            mail.login(config.mailAddress, config.password)
            mail.sendmail(config.mailAddress, config.sendTo, content.encode("utf-8"))
        
        
        # BEAR EVENT
        if kesisim and df["Fast Ema"][len(df.index)-1] < df["Slow Ema"][len(df.index)-1] and shortPozisyonda == False:
            if longPozisyonda:
                print("LONG İŞLEMDEN ÇIKILIYOR...")
                satilacakMiktar = float(position_bilgi["positionAmt"][len(position_bilgi.index) - 1])
                longExit(satilacakMiktar)
            alinacak_miktar = (((float(free_balance["USDT"]) / 100 ) * float(islemeGirecekPara)) * float(leverage)) / float(df["close"][len(df.index) - 1])
            print ("SHORT İŞLEME GİRİLİYOR...")
            shortEnter(alinacak_miktar)
            takeprofit1 = False
            takeprofit1 = False
            baslik = symbol
            message = "SHORT ENTER\n" + "Toplam Para: " + str(balance['total']["USDT"])
            content = f"Subject: {baslik}\n\n{message}"
            mail = SMTP("smtp.gmail.com", 587)
            mail.ehlo()
            mail.starttls()
            mail.login(config.mailAddress, config.password)
            mail.sendmail(config.mailAddress, config.sendTo, content.encode("utf-8"))
 
        # STOP LOSS FOR LONG POSITION
        if longPozisyonda and ((float(df["close"][len(df.index)-1]) - float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1])) / float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1])) * 100 * -1 >= float(stopLoss):
            print ("STOP LOSS")
            satilacakMiktar = (float(position_bilgi["positionAmt"][len(position_bilgi.index) - 1]))
            longExit(satilacakMiktar)
            takeprofit1 = False
            takeprofit1 = False
            baslik = symbol
            message = "LONG EXIT (STOP LOSS)\n" + "Toplam Para: " + str(balance['total']["USDT"])
            content = f"Subject: {baslik}\n\n{message}"
            mail = SMTP("smtp.gmail.com", 587)
            mail.ehlo()
            mail.starttls()
            mail.login(config.mailAddress, config.password)
            mail.sendmail(config.mailAddress, config.sendTo, content.encode("utf-8")) 
        
        # STOP LOSS FOR SHORT POSITION
        if shortPozisyonda and ((float(df["close"][len(df.index)-1]) - float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1])) / float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1])) * 100 >= float(stopLoss):
            print ("STOP LOSS")
            satilacakMiktar = (float(position_bilgi["positionAmt"][len(position_bilgi.index) - 1]))
            shortExit(satilacakMiktar)
            takeprofit1 = False
            takeprofit1 = False
            baslik = symbol
            message = "LONG EXIT (STOP LOSS)\n" + "Toplam Para: " + str(balance['total']["USDT"])
            content = f"Subject: {baslik}\n\n{message}"
            mail = SMTP("smtp.gmail.com", 587)
            mail.ehlo()
            mail.starttls()
            mail.login(config.mailAddress, config.password)
            mail.sendmail(config.mailAddress, config.sendTo, content.encode("utf-8")) 
        
        # TAKE PROFIT FOR LONG POSITION
        # TAKE PROFIT 1
        if longPozisyonda and takeprofit1 == False and ((float(df["close"][len(df.index)-1]) - float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1])) / float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1])) * 100 >= float(tp1):
            print ("TAKE PROFIT 1")
            satilacakMiktar = (float(position_bilgi["positionAmt"][len(position_bilgi.index) - 1])) / 2
            longExit(satilacakMiktar)
            takeprofit1 = True
            baslik = symbol
            message = "LONG EXIT (TAKE PROFIT 1)\n" + "Toplam Para: " + str(balance['total']["USDT"])
            content = f"Subject: {baslik}\n\n{message}"
            mail = SMTP("smtp.gmail.com", 587)
            mail.ehlo()
            mail.starttls()
            mail.login(config.mailAddress, config.password)
            mail.sendmail(config.mailAddress, config.sendTo, content.encode("utf-8"))
        
        # TAKE PROFIT 2
        if longPozisyonda and takeprofit2 == False and ((float(df["close"][len(df.index)-1]) - float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1])) / float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1])) * 100 >= float(tp2):
            print ("TAKE PROFIT 2")
            satilacakMiktar = float(position_bilgi["positionAmt"][len(position_bilgi.index) - 1])
            longExit(satilacakMiktar)
            takeprofit2 = True
            baslik = symbol
            message = "LONG EXIT (TAKE PROFIT 2)\n" + "Toplam Para: " + str(balance['total']["USDT"])
            content = f"Subject: {baslik}\n\n{message}"
            mail = SMTP("smtp.gmail.com", 587)
            mail.ehlo()
            mail.starttls()
            mail.login(config.mailAddress, config.password)
            mail.sendmail(config.mailAddress, config.sendTo, content.encode("utf-8"))
        
        # TAKE PROFIT FOR SHORT POSITION
        # TAKE PROFIT 1
        if shortPozisyonda and takeprofit1 == False and ((float(df["close"][len(df.index)-1]) - float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1])) / float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1])) * 100 * -1 >= float(tp1):
            print ("TAKE PROFIT 1")
            satilacakMiktar = (float(position_bilgi["positionAmt"][len(position_bilgi.index) - 1])) / 2
            shortExit(satilacakMiktar)
            takeprofit1 = True
            baslik = symbol
            message = "LONG EXIT (TAKE PROFIT 1)\n" + "Toplam Para: " + str(balance['total']["USDT"])
            content = f"Subject: {baslik}\n\n{message}"
            mail = SMTP("smtp.gmail.com", 587)
            mail.ehlo()
            mail.starttls()
            mail.login(config.mailAddress, config.password)
            mail.sendmail(config.mailAddress, config.sendTo, content.encode("utf-8"))
        
        # TAKE PROFIT 2
        if shortPozisyonda and takeprofit2 == False and ((float(df["close"][len(df.index)-1]) - float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1])) / float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1])) * 100 * -1 >= float(tp2):
            print ("TAKE PROFIT 2")
            satilacakMiktar = float(position_bilgi["positionAmt"][len(position_bilgi.index) - 1])
            shortExit(satilacakMiktar)
            takeprofit2 = True
            baslik = symbol
            message = "LONG EXIT (TAKE PROFIT 2)\n" + "Toplam Para: " + str(balance['total']["USDT"])
            content = f"Subject: {baslik}\n\n{message}"
            mail = SMTP("smtp.gmail.com", 587)
            mail.ehlo()
            mail.starttls()
            mail.login(config.mailAddress, config.password)
            mail.sendmail(config.mailAddress, config.sendTo, content.encode("utf-8"))
        
        if pozisyondami == False:
            print("POZİSYON ARANIYOR...")

        if shortPozisyonda:
            print("SHORT POZİSYONDA BEKLİYOR")
            print("PRICE: ", float(df["close"][len(df.index)-1]))
            print("STOP LOSS PRICE: ", ((float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1]) / 100 ) * float(stopLoss)) + float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1]))
            print("TAKE PROFIT 1 PRICE: ", float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1])-(float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1])/100) * float(tp1))
            print("TAKE PROFIT 2 PRICE: ", float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1])-(float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1])/100) * float(tp2))
 
        if longPozisyonda:
            print("LONG POZİSYONDA BEKLİYOR")
            print("PRICE: ", float(df["close"][len(df.index)-1]))
            print("STOP LOSS PRICE: ", float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1])-(float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1])/100) * float(stopLoss))
            print("TAKE PROFIT 1 PRICE: ", ((float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1]) / 100 ) * float(tp1)) + float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1]))
            print("TAKE PROFIT 2 PRICE: ", ((float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1]) / 100 ) * float(tp2)) + float(position_bilgi["entryPrice"][len(position_bilgi.index) - 1]))
        
        print("==============================================================================================================")
    
    except ccxt.BaseError as Error:
        print ("[ERROR] ", Error )
        continue
