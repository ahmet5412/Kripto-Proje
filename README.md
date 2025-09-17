# Kripto Analiz Aracı

Bu proje, CoinGecko API'sinden aldığı verilerle basit teknik analizler yapan ve sonuçları grafiklerle birlikte sunan bir masaüstü uygulamasıdır. Uygulama Tkinter tabanlıdır ve hareketli ortalamalar, RSI gibi göstergeler içerir.

## Özellikler

- Bitcoin, Ethereum gibi popüler kripto paralar arasından seçim yapma
- 7 gün ile 1 yıl arasında farklı zaman aralıkları
- CoinGecko üzerinden canlı fiyat ve hacim verisi çekme
- SMA, EMA, RSI ve volatilite hesaplamaları
- Fiyat ve RSI grafiklerini tek ekranda görme
- Analiz sonuçlarını CSV olarak dışa aktarma

## Gereksinimler

- Python 3.10 veya üzeri
- İnternet bağlantısı (CoinGecko verileri için)

Gerekli Python paketleri `requirements.txt` dosyasında listelenmiştir.

```bash
pip install -r requirements.txt
```

## Kullanım

1. Depoyu klonlayın veya bu dosyaları yerel ortamınıza indirin.
2. Bağımlılıkları yükleyin.
3. Uygulamayı aşağıdaki komutla başlatın:

```bash
python main.py
```

Uygulama açıldığında istediğiniz kripto parayı, para birimini (varsayılan: USD) ve zaman aralığını seçip **Analiz Et** butonuna tıklayabilirsiniz. Analiz tamamlandığında grafikler ve metinsel özet görüntülenir. Sonuçları CSV olarak kaydetmek için **CSV Dışa Aktar** butonunu kullanabilirsiniz.

## Notlar

- CoinGecko API'sinin hız limitlerine takılmamak için art arda çok sayıda istek göndermekten kaçının.
- RSI 70 seviyesinin üzerinde ise aşırı alım, 30 seviyesinin altında ise aşırı satım olarak yorumlanır. Bu veriler yatırım tavsiyesi değildir.

## Lisans

MIT Lisansı altında yayınlanmıştır.
