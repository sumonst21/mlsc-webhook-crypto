Tradingview Webhook Crypto Heroku
------------------------------------------

The application receives webhook alerts from the tradingview platform for the crypto market in a JSON format and place orders according to the instructions received.


Configuration Files:
---------

- create virtual environment

      virtualenv mlsc-binance
      mlsc-binance\Scripts\activate
      
- install dependences

      pip3 install -r requirements.txt
  
Strategies:
----------
- sma cross - (fast x slow)
  
Exchanges:
---------
- Binance

Technologies:
---------
- Python
- Flask
- Heroku
