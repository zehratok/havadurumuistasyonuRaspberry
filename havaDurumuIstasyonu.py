import time
import datetime
import board
import adafruit_dht
import sys
import smtplib
import gpiozero
import RPi.GPIO as GPIO
from pyrebase import pyrebase
from gpiozero import InputDevice
from time import sleep
import Adafruit_BMP.BMP085 as BMP085
import smbus2
import math


# sensörlerin bağlanacağı pinler tanımlandı:
dhtDevice = adafruit_dht.DHT11(board.D14) # DHT11 sensörü
noRainDevice = InputDevice(10) # Yağmur sensörü
bmp180 = BMP085.BMP085() # BMP180 Basınç sensörü
bus = smbus2.SMBus(1) #Pusula sensörü
address = 0x77 #Pusula sensörü

# Firebase konfigürasyonu yapıldı
config = {
   "apiKey": "AIzaSyAGssZ1n3twNvzoa-uUF7Q0udeoJILTb2I",
    "authDomain": "havadurumuistasyonu.firebaseapp.com",
    "databaseURL": "https://havadurumuistasyonu-default-rtdb.firebaseio.com",
    "storageBucket":"havadurumuistasyonu.appspot.com"
}

firebase = pyrebase.initialize_app(config)
db = firebase.database()

# Pusula sensörü için fonksiyonlar tanımlandı:
def read_word_2c(adr):
    high = bus.read_byte_data(address, adr)
    low = bus.read_byte_data(address, adr+1)
    val = (high << 8) + low
    if (val >= 0x8000):
        return -((65535 - val) + 1)
    else:
        return val

# Pusula sensörü için gerekli ayarlamalar yapıldı:
bus.write_byte_data(address, 0, 0b01110000)

# Sensörlerden verilerin okunması :

while True:
    current_time = datetime.datetime.now().strftime("%H:%M:%S") #Saat bilgisi alındı
    if current_time.endswith(":00:00") and current_time != "00:00:00": # Her saat başı verilerin alınması için koşul oluşturuldu
        try:
            temperature_c = dhtDevice.temperature # Sıcaklık bilgisi alındı
            if noRainDevice.is_active == True: # Yağmur sensörü aktifse
                isRain = False # Yağmur yok
            else : # Yağmur sensörü aktif değilse
                isRain = True  # Yağmur var

        except RuntimeError as error: # Hata oluşursa
            print(error.args[0]) # Hata mesajı yazdırılır
            time.sleep(2.0) # 2 saniye bekle
            continue # Döngüye devam et
        except Exception as error: # Hata oluşursa
            dhtDevice.exit() # DHT11 sensörünü kapat
            raise error # Hata mesajı yazdır
            continue     # Döngüye devam et
        if isRain == True: # Yağmur varsa
            if temperature_c >= 18 : # Sıcaklık 18 dereceden büyükse
                weatherStatus = "Yağışlı" # Hava yağışlı
                icon = "yagisli" # Hava durumu ikonu yagisli
            else: # Sıcaklık 18 dereceden küçükse
                weatherStatus = "Gök Gürültülü Sağanak Yağışlı" # Hava gök gürültülü sağanak yağışlı
                icon = "gokGurultulu" # Hava durumu ikonu gokGurultulu
        else : # Yağmur yoksa
            if temperature_c >= 18 : # Sıcaklık 18 dereceden büyükse
                weatherStatus = "Güneşli" # Hava güneşli
                icon = "günesli" # Hava durumu ikonu güneşli
            else: # Sıcaklık 18 dereceden küçükse
                weatherStatus = "Parçalı Bulutlu" # Hava parçalı bulutlu
                icon = "parcaliBulutlu" # Hava durumu ikonu parçalı bulutlu
        hourlyData = { # Saatlik sıcaklık bilgisi için nesne oluşturuldu
        "temperature_c": str(temperature_c),
        "icon": str(icon),
        "time": datetime.datetime.now().strftime("%H:%M"),
        }
        db.child("Hourly_Temp_Result").push(hourlyData) # Firebase veritabanına saatlik sıcaklık bilgisi eklendi
    try:
        temperature_c = dhtDevice.temperature # Sıcaklık bilgisi alındı
        temperature_f = temperature_c * (9 / 5) + 32 # Sıcaklık bilgisi Fahrenheit cinsine çevrildi
        humidity = dhtDevice.humidity # Nem bilgisi alındı
        pressure_pa = bmp180.read_pressure() # Basınç bilgisi alındı
        pressure_hpa = pressure_pa / 100 # Basınç bilgisi hektopaskal cinsine çevrildi
        x_out = read_word_2c(3) # Pusula sensöründen x ekseninden veri okundu
        y_out = read_word_2c(7) # Pusula sensöründen y ekseninden veri okundu
        z_out = read_word_2c(5) # Pusula sensöründen z ekseninden veri okundu
        # Pusula yönünü hesapla
        heading = (180 * math.atan2(y_out, x_out)) / math.pi
        if heading < 0: # Pusula yönü 0'dan küçükse
            heading += 360 # Pusula yönü 360 derece eklenerek güncelle
        if noRainDevice.is_active == True: # Yağmur sensörü aktifse
            isRain = False # Yağmur yok
            rain = 0 # Yağış miktarı 0
        else: # Yağmur sensörü aktif değilse
            isRain = True # Yağmur var
            rain= humidity * 5 # Yağış miktarı nem miktarının 5 katı

    except RuntimeError as error: # Hata oluşursa
        print(error.args[0]) # Hata mesajı yazdırılır
        time.sleep(2.0) # 2 saniye bekle
        continue # Döngüye devam et
    except Exception as error: # Hata oluşursa
        dhtDevice.exit() # DHT11 sensörünü kapat
        raise error # Hata mesajı yazdır
        continue    # Döngüye devam et

    time.sleep(5.0) # 5 saniye bekle

    if isRain == True: # Yağmur varsa
        if temperature_c >= 18 : # Sıcaklık 18 dereceden büyükse
            weatherStatus = "Yağışlı" # Hava yağışlı
            icon = "yagisli" # Hava durumu ikonu yagisli
        else:   # Sıcaklık 18 dereceden küçükse
            weatherStatus = "Gök Gürültülü Sağanak Yağışlı" # Hava gök gürültülü sağanak yağışlı
            icon = "gokGurultulu" # Hava durumu ikonu gokGurultulu
    else : # Yağmur yoksa
        if temperature_c >= 18 : # Sıcaklık 18 dereceden büyükse
            weatherStatus = "Güneşli" # Hava güneşli
            icon = "günesli" # Hava durumu ikonu güneşli
        else:   # Sıcaklık 18 dereceden küçükse
            weatherStatus = "Parçalı Bulutlu" # Hava parçalı bulutlu
            icon = "parcaliBulutlu" # Hava durumu ikonu parçalı bulutlu
    tempData = {        # hava durumu datası için nesne oluşturuldu
        "temperature_c": str(temperature_c), # Sıcaklık bilgisi eklendi C cinsinden
        "temperature_f": str(temperature_f), # Sıcaklık bilgisi eklendi F cinsinden
        "humidity": str(humidity), # Nem bilgisi eklendi
        "pressure": int(pressure_hpa), # Basınç bilgisi eklendi
        "weatherStatus": str(weatherStatus), # Hava durumu bilgisi eklendi
        "rain":str(rain), # Yağış miktarı bilgisi eklendi
        "windDirection": int(heading), # Rüzgar yönü bilgisi eklendi
        "icon": str(icon), # Hava durumu ikonu eklendi
        "time": datetime.datetime.now().strftime("%H:%M:%S"), # Saat bilgisi eklendi
        "date": datetime.datetime.now().strftime("%Y-%m-%d"), # Tarih bilgisi eklendi
    }

    db.child("Temp_Result").set(tempData) # Firebase veritabanında Temp_Result tablosuna hava durumu bilgisi eklendi
    db.child("Temp_Time_Result").child(tempData["date"]).child(tempData["time"]).push(tempData) # Firebase veritabanında Temp_Time_Result tablosuna tarih ve saat bilgisi eklendi

    print(tempData) # Hava durumu bilgisi yazdırıldı



