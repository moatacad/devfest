class Config:
    APP_NAME="New Year App"
    
    
class LiveConfig(Config):
    DBNAME="live"
    DBPWD = "live1234"
    
class TestConfig(Config):
    DBNAME="test"
    DBPWD='test1234'
  
    


    