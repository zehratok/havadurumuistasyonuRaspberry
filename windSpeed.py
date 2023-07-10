import cv2
import numpy as np
import time

# Kamera girişini başlat
cap = cv2.VideoCapture(0)  # Kamera numarasını buraya göre ayarlayın, genellikle 0 veya 1

# Önceki frame'i saklamak için değişkenler
previous_frame = None

# Ölçek faktörü (renk değişim hızı -> rüzgar hızı dönüşümü için)
scale_factor = 0.1  # Ölçek faktörünü deneyerek belirleyin

# Zamanı takip etmek için değişkenler
previous_time = time.time()
average_wind_speed = 0
count = 0

# Sonsuz döngü içinde kameradan görüntü alınır
while True:
    # Kameradan bir frame alınır
    ret, frame = cap.read()

    # Gri tonlamalı görüntü elde edin
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Önceki frame mevcut değilse, önceki frame'i güncelleyin ve döngünün bir sonraki adımına geçin
    if previous_frame is None:
        previous_frame = gray_frame
        continue

    # İki frame arasındaki farkı hesaplayın
    frame_diff = cv2.absdiff(previous_frame, gray_frame)

    # Fark görüntüsünü eşikleyin (isteğe bağlı)
    _, thresh = cv2.threshold(frame_diff, 30, 255, cv2.THRESH_BINARY)

    # Renk değişim hızını hesaplamak için piksel değerlerini toplayın
    color_change_speed = np.sum(thresh) / 255

    # Geçen süreyi hesaplayın
    current_time = time.time()
    elapsed_time = current_time - previous_time

    # Dönme hızını hesaplayın (renk değişim hızı / geçen süre)
    rotation_speed = color_change_speed / elapsed_time

    # Renk değişim hızını rüzgar hızına dönüştürün (örneğin, dönme hızı olarak RPM)
    wind_speed = rotation_speed * scale_factor

    # Toplam rüzgar hızını güncelleyin
    average_wind_speed += wind_speed
    count += 1

    # Her 5 saniyede bir ortalama rüzgar hızını yazdırın
    if current_time - previous_time >= 1:
        average_wind_speed /= count
        print("Ortalama Rüzgar Hızı: {} RPM".format(average_wind_speed))
        average_wind_speed = 0
        count = 0
        previous_time = current_time

    # Önceki frame'i güncelleyin
    previous_frame = gray_frame

    # Ekran görüntüsünü gösterin
    cv2.imshow("Kamera", frame)

    # Çıkış tuşuna basıldığında döngüyü sonlandır
    if cv2.waitKey(1) == 27:  # ESC tuşuna basarak çıkabilirsiniz
        break

# Kaynakları serbest bırakın ve pencereyi kapatın
cap.release()
cv2.destroyAllWindows()
