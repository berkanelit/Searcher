import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
import threading

# Özetleme için transformers pipeline'ı yükle
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")

# Google'dan veri çeken ve özetleyen fonksiyon
def fetch_and_summarize(query, output_box, progress_bar):
    url = f"https://www.google.com/search?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    # Google sonuçlarını bul
    results = soup.find_all("div", class_="tF2Cxc")
    combined_content = ""

    progress_bar["value"] = 0
    progress_step = 100 / min(5, len(results))  # İlerleme barı için adım hesapla

    # İlk 5 siteye giriş yap ve içerikleri birleştir
    for idx, result in enumerate(results[:5], start=1):
        try:
            title = result.find("h3").text
            link = result.find("a")["href"]
            
            # Site içeriğini çek
            site_response = requests.get(link, headers=headers)
            site_soup = BeautifulSoup(site_response.text, "html.parser")
            
            # Paragrafları bul ve birleştir
            paragraphs = site_soup.find_all("p")
            content = " ".join([para.text for para in paragraphs if para.text])
            
            if content:
                combined_content += content + " "
                output_box.insert(tk.END, f"{idx}. Siteden içerik alındı: {title}\n")
            else:
                output_box.insert(tk.END, f"{idx}. Sitede içerik bulunamadı: {title}\n")
        except Exception as e:
            output_box.insert(tk.END, f"{idx}. Sitede hata oluştu: {e}\n")
        finally:
            progress_bar["value"] += progress_step

    # Eğer birleştirilmiş içerik boş değilse özetle
    if combined_content.strip():
        try:
            # Metni 1024 token sınırında kırp
            max_input_length = 1024
            combined_content = combined_content[:max_input_length]

            # Özetleme
            summary = summarizer(combined_content, max_length=300, min_length=100, do_sample=False)
            summary_text = summary[0]["summary_text"]
            
            # Özet çıktısını arayüze yazdır
            output_box.insert(tk.END, "\nÖzet:\n")
            output_box.insert(tk.END, summary_text + "\n")
            
            # Özet çıktısını dosyaya kaydet
            with open("site_ozetleri.txt", "w", encoding="utf-8") as f:
                f.write("Özet:\n")
                f.write(summary_text + "\n")
            output_box.insert(tk.END, "Tüm özetler 'site_ozetleri.txt' dosyasına kaydedildi.\n")
        except Exception as e:
            output_box.insert(tk.END, f"Özetleme sırasında hata oluştu: {e}\n")
    else:
        output_box.insert(tk.END, "Hiçbir siteden içerik alınamadı, özetleme yapılmadı.\n")
    progress_bar["value"] = 100  # İşlem tamamlandı

# Arayüz tasarımı
def create_gui():
    def on_search():
        query = search_entry.get()
        if not query.strip():
            messagebox.showwarning("Uyarı", "Lütfen bir arama terimi girin!")
            return
        
        # Arama işlemini arayüzde dondurmamak için bir thread içinde çalıştır
        output_box.delete(1.0, tk.END)  # Çıktı kutusunu temizle
        progress_bar["value"] = 0  # İlerleme çubuğunu sıfırla
        threading.Thread(target=fetch_and_summarize, args=(query, output_box, progress_bar), daemon=True).start()

    # Ana pencere
    root = tk.Tk()
    root.title("Google Özetleme Aracı")
    root.geometry("800x600")
    root.configure(bg="#f9f9f9")

    # Stil ayarları
    style = ttk.Style()
    style.configure("TButton", font=("Arial", 12))
    style.configure("TLabel", font=("Arial", 12))
    style.configure("TProgressbar", thickness=10)

    # Üst kısım (Arama terimi ve buton)
    top_frame = tk.Frame(root, bg="#f9f9f9")
    top_frame.pack(pady=10)

    tk.Label(top_frame, text="Arama Terimi:", bg="#f9f9f9", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=10, sticky="w")
    search_entry = ttk.Entry(top_frame, width=50, font=("Arial", 12))
    search_entry.grid(row=0, column=1, padx=10, pady=10)
    search_button = ttk.Button(top_frame, text="Ara", command=on_search)
    search_button.grid(row=0, column=2, padx=10, pady=10)

    # Orta kısım (İlerleme çubuğu ve çıktı kutusu)
    progress_bar = ttk.Progressbar(root, orient="horizontal", mode="determinate", length=600)
    progress_bar.pack(pady=10)

    output_box = scrolledtext.ScrolledText(root, width=90, height=25, font=("Courier", 10), wrap=tk.WORD)
    output_box.pack(pady=10)

    # Pencereyi başlat
    root.mainloop()

# Arayüzü başlat
if __name__ == "__main__":
    create_gui()
