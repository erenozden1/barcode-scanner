# ITF Barkod Okuyucu

# Özet:

	Gereksinimler

* 20 cm – 150 cm mesafe aralığında çalışma.

* ITF (Interleaved 2 of 5\) barkodları okuyabilme

* Açılı (eğik) okuma yeteneği.

Donanım Fikirleri

* Kamera otofokuslu olabilir, böylece farklı uzaklıklardaki barkodları okuyabilir.

* Dar görüş açılı, varifocal(ayarlanabilir odaklı)  lens  \-\> uzun odak uzaklığı sağlar, uzak okumalarda bar başına düşen piksel sayısı artar

* Çapraz polarizasyon (yansımayı engellemek adına) \-\> Işıklandırma yeterli değil ise çekilecek LED’Lerin önüne polarize film yerleştirilebilir. Kamera için de aynı polarize film ya da Circular Polarizing (CPL) filtre kullanılabilir.

[https://www.amazon.com/ELP-8mp-Microphone-Autofocus-Surveillance/dp/B0CG4BYL7Z](https://www.amazon.com/ELP-8mp-Microphone-Autofocus-Surveillance/dp/B0CG4BYL7Z) \- 1500TL

**Yazılım süreci:** OpenCV THY’nin bagajlar için kullandığı ITF tipindeki barkodları çözümleyememekte. Bu nedenle projenin ilk aşamasında denediklerim sonucunda barkodları okumayı başaramadım ve sorunu anlayamadım. Sorunun kütüphanenin kendisinde olmasını anlamam uzun sürdü. Bunu fark etmemin ardından ZXing tarafından hazırlanan eklentiyi kullanarak bu sorunu bertaraf ettim. Kamera ekipmanlarının yetersizliğinden dolayı yazılımımın ne kadar optimize olduğunu tam olarak test edemedim, iPhoneların kendi barkod okuma uygulamasına seviyesinde sonuçlar almaya başladığımda başarılı olduğum sonucuna vardım. iPhone kamerasının çözünürlüğü ve fokus yapmak için kullanıcının girdisine ihtiyaç duyuyor olması bu kameraların bu amaçla kullanılamayacak olduğunu gösteriyor. Raporun devamında en optimize sistem için gerekli her şey inceleniyor.

# Nasıl Çalıştırılır

Python 3 ve bir kamera gerekir (Windows üzerinde geliştirildi).

```
pip install -r requirements.txt
cd src
python frameSelector.py
```

* `frameSelector.py`, DirectShow ile `1` numaralı kamerayı açar (`cv2.VideoCapture(1, cv2.CAP_DSHOW)`). Tek kameranız varsa ya da Windows kullanmıyorsanız bu satırı değiştirin, örn. `cv2.VideoCapture(0)`.
* Program, `barcodeDetector.py` içindeki `EXPECTED_BARCODE_TEXT` değerine eşit bir barkod okuduğunda durur. Bu değeri kendi test etiketinizdeki numarayla değiştirin.
* Çıkmak için `q` tuşuna basın.

# 1\. Proje Gereksinimleri

* ITF (Interleaved 2 of 5\) barkodlarını endüstriyel güvenilirlikte okuma — uçak bagaj etiketlerindeki IATA numaraları ITF formatındadır.

* 20 cm – 150 cm mesafe aralığında çalışma.

* Açılı (eğik) okuma yeteneği.

* Yazılım: OpenCV (görüntü işleme) \+ ZBar veya ZXing-C++ (barkod çözümleme).

* Toplam bütçe: yaklaşık 100 $.

# 2\. Temel Tasarım Kararları

## 2.1 Otofokus Zorunlu, Motorlu Zoom Gereksiz

Barkodun mesafesi değiştiğinde iki şey olur: görüntü netliği bozulur (bu okumayı gerçekten engeller) ve barkod karede küçülür/büyür (bu genellikle sorun yaratmaz). Bu nedenle değişen mesafe problemi otomatik odak (otofokus) ile çözülür; otomatik odak uzaklığı (motorlu zoom) gerekmez.

## 2.2 Lens Seçimi: Dar Görüş Açısı

Dar lens (uzun odak uzaklığı), sensörün sabit piksel sayısını daha küçük bir sahne alanına yoğunlaştırır; böylece 150 cm'de bar başına düşen piksel sayısı artar. Geniş lens ise pikselleri geniş alana yayar ve ince ITF barları çözülemez hale gelir.

Hesap: 4000 piksel genişliğinde sensör, 65° lens ile 150 cm'de piksel başına \~0,48 mm görür — en ince ITF barları (0,25–0,5 mm) için sınırda. Aynı sensör \~40° lens ile \~0,27 mm/piksel değerine ulaşır — rahat bölge. Bu yüzden mümkünse dar lens varyantı tercih edilmelidir.

Sabit odaklı lens şart değildir: varifocal lens (örn. 5–50 mm) kurulumda elle ayarlanıp kilitlenir ve deneme özgürlüğü sağlar. Odak uzaklığı (zoom halkası) ile netlik (focus halkası) ayrı ayarlardır.

## 2.3 Monokrom vs Renkli Sensör

Monokrom sensör barkod için optik olarak üstündür: Bayer filtresi olmadığından kenarlar daha keskin, ışık hassasiyeti 2–3 kat daha iyidir. Ancak bütçe sınıfında otofokuslu monokrom modül bulmak zordur. 20–150 cm aralığı otofokus gerektirdiğinden pratik seçim: renkli otofokuslu kamera \+ yazılımda gri tona çevirme.

# 3\. Aydınlatma ve Açılı Okuma

## 3.1 Parlama (Glare) Problemi

Bagaj etiketleri sentetik kaplamalı termal kağıttır (yarı parlak yüzey). Açılı okumada başarısızlığın ana nedeni geometri değil, parlak yüzeyden yansıyan ışığın barları beyaza boğmasıdır.

## 3.2 Çapraz Polarizasyon (Önerilen)

* LED'lerin önüne bir yönde, lensin önüne 90° döndürülmüş polarize film yerleştirilir.

* Aynasal yansımalar polarizasyonu korur ve lens filtresinde engellenir; barkod kontrastını taşıyan dağınık ışık geçer.

* Maliyet: \~10–15 $ (yapışkanlı film tabakası). Işığın \~%60'ını yuttuğu için LED gücü 2–3 kat artırılmalıdır.

## 3.3 Parlak Ortamda Çalışma

Çapraz polarizasyon yalnızca kendi LED'lerinizin ışığında etkilidir; ortam ışığı polarize değildir. Çözüm: pozlama süresini \~0,5–1 ms'ye düşürüp yakın ve güçlü LED kullanmak — kamera ağırlıklı olarak sizin polarize ışığınızı görür. Bu ayrıca hareket bulanıklığını da çözer. Mümkünse tarama bölgesine basit bir gölgelik/siperlik eklemek en ucuz ve sağlam çözümdür.

## 3.4 LED Yerleşimi

LED'ler lens ekseninden 30–45° açıyla yerleştirilmelidir; bu tek başına doğrudan parlamanın çoğunu önler. Difüzörlü LED bar veya panel tercih edin.

# 4\. Bagaj Etiketine Özgü Zorluklar

* **Kıvrılmış/bükülmüş etiket:** Etiketler sapa sarıldığı için barkod düz durmaz. Etikette barkod birden çok yönde basılıdır; yazılım karedeki tüm barkod örneklerini denemelidir. Ağır kıvrımda OpenCV ile bölge tespiti \+ perspektif/silindirik düzeltme gerekebilir.

* **150 cm'de çözünürlük:** IATA spesifikasyonu ince barı \~0,25–0,5 mm'ye izin verir; güvenilir çözümleme için bar başına \~2 piksel gerekir. Bu, 150 cm'de yatay görüş alanını \~50–60 cm ile sınırlar — tarama bölgesi tanımlı olmalıdır.  
* **Gerçekçi değerlendirme:** 20–80 cm aralığında işbirlikli sunumla 100 $ sistem iyi çalışır. 150 cm'de kıvrık, parlak ve hareketli etiketi güvenilir okumak endüstriyel sistemlerin binlerce dolar harcadığı bölgedir; 150 cm hedefi gerçek etiketlerle erkenden doğrulanmalıdır.

# 5\. Kamera Karşılaştırması

| Model | Sensör / Çözünürlük | Otofokus | Fiyat / Not |
| :---- | :---- | :---- | :---- |
| ELP 12MP (IMX362) | 1/2.55", 4000×3000 | PDAF, \~300 ms (hızlı) | \~70–80 $ — hareketli bagaj için önerilen |
| ELP 12MP (IMX577) | 1/2.3", 3840×3040 | Kontrast AF (daha yavaş) | Değiştirilebilir M12 lens (2.1–25 mm) |
| ELP 8MP (IMX179) | 3840×2160 | Otofokus | \~60 $ — bütçe seçeneği |
| Arducam IMX519 16MP | 4656×3496 | Otofokus | \~30–46 $ — Raspberry Pi gerektirir |

Öneri: Hareketli bagaj için ELP 12MP IMX362 (PDAF) — hızlı faz algılamalı otofokus. Lens esnekliği isteniyorsa IMX577 sürümü (12/16 mm M12 lens seçeneğiyle). 65° lens varyantı 76°'ye tercih edilmelidir.

# 6\. Bütçe Özeti

| Bileşen | Tahmini Fiyat | Not |
| :---- | :---- | :---- |
| ELP 12MP PDAF Otofokus Kamera (IMX362) | 70–80 $ | Ana öneri |
| LED aydınlatma (difüzörlü bar/panel) | 15–20 $ | Polarize film kaybını telafi için güçlü seçin |
| Lineer polarize film (2'li paket) | 10–15 $ | Çapraz polarizasyon için |
| **TOPLAM** | **\~95–115 $** | Bütçe sınırında |

# 7\. Satın Alma Bağlantıları

## 7.1 Perakende

* ELP 12MP PDAF (IMX362), Amazon: amazon.com/dp/B0DQNP1MP9 (\~70–80 $)

* ELP 12MP IMX577 (değiştirilebilir M12 lens): svpro.cc/product/2008

* ELP 8MP otofokus (IMX179), Amazon: amazon.com/dp/B0C23C5NHS (\~60 $)

* Arducam IMX519 16MP (Raspberry Pi): amazon.com/dp/B09STL7S88 (\~35–46 $)

* Polarize film (2'li, yapışkanlı): amazon.com/dp/B0BS6FMZNL (\~10–15 $)

* LED: Amazon'da "12V LED bar light diffused" araması (\~15–20 $)

## 7.2 Toplu Alım (B2B)

ELP kameraların üreticisi Shenzhen Ailipu Technology Co., Ltd.'dir (2005'ten beri; CE, FCC, RoHS, UL, ISO sertifikalı). OEM/ODM ve özelleştirme kabul eder — hacimli siparişte istediğiniz lens/sensör kombinasyonu üretilebilir.

* Doğrudan: elpcctv.com — sales@elpcctv.com

* Alibaba mağazası: elpcctv.en.alibaba.com (Trade Assurance önerilir)

* Made-in-China: ellipe.en.made-in-china.com

* Tipik MOQ: özel üretimde 50–100 adet; standart modellerde 20–50 adette indirim başlar (perakendeye göre \~%30–50 daha ucuz).

* Polarize film toptan: 3dlens.com; endüstriyel sınıf: apioptics.com, MidOpt.

B2B tavsiyesi: MOQ taahhüdünden önce 2–3 numune sipariş edip gerçek bagaj etiketleriyle 150 cm'de doğrulayın. Otofokuslu ve sabit odaklı varyantlar birbirine çok benzer; sipariş formunda tam model kodunu ve lens görüş açısını açıkça belirtin.

# 8\. Yazılım Mimarisi (Özet)

* OpenCV: görüntü yakalama, gri ton, adaptif eşikleme, eğrilik/perspektif düzeltme, merkez bölge kırpma (dijital zoom).

* Çözümleme: ZBar veya ZXing-C++ (ITF çözücüyü sıfırdan yazmayın).

* Monokrom kamera kullanılırsa: kare tek kanallı gelir; gerekirse CAP\_PROP\_CONVERT\_RGB \= 0 ayarlayın.

* Karedeki tüm barkod adaylarını deneyin (bagaj etiketinde barkod birden çok kez basılıdır).