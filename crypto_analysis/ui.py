"""Tkinter tabanlı kripto analiz arayüzü."""
from __future__ import annotations

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from typing import Dict

import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .analysis import build_summary, enrich_with_indicators
from .api import CoinGeckoError, MarketData, fetch_market_chart

POPULAR_COINS: Dict[str, str] = {
    "Bitcoin (BTC)": "bitcoin",
    "Ethereum (ETH)": "ethereum",
    "Binance Coin (BNB)": "binancecoin",
    "Ripple (XRP)": "ripple",
    "Cardano (ADA)": "cardano",
    "Solana (SOL)": "solana",
    "Dogecoin (DOGE)": "dogecoin",
    "Polkadot (DOT)": "polkadot",
    "Litecoin (LTC)": "litecoin",
    "Avalanche (AVAX)": "avalanche-2",
}

TIMEFRAME_OPTIONS: Dict[str, int] = {
    "7 Gün": 7,
    "14 Gün": 14,
    "1 Ay": 30,
    "3 Ay": 90,
    "6 Ay": 180,
    "1 Yıl": 365,
}


class CryptoAnalyzerApp:
    """Ana uygulama sınıfı."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Kripto Analiz Aracı")
        self.root.geometry("1100x700")
        self.root.minsize(960, 640)

        self.coin_var = tk.StringVar(value=next(iter(POPULAR_COINS)))
        self.currency_var = tk.StringVar(value="usd")
        self.timeframe_var = tk.StringVar(value="1 Ay")

        self._latest_data: pd.DataFrame | None = None
        self._analysis_thread: threading.Thread | None = None

        self._build_layout()

    # ------------------------------------------------------------------
    # UI Kurulumu
    # ------------------------------------------------------------------
    def _build_layout(self) -> None:
        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(control_frame, text="Kripto Para:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        coin_combo = ttk.Combobox(control_frame, textvariable=self.coin_var, values=list(POPULAR_COINS.keys()), state="readonly")
        coin_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(control_frame, text="Karşılık Birimi:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        currency_entry = ttk.Entry(control_frame, textvariable=self.currency_var, width=10)
        currency_entry.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)

        ttk.Label(control_frame, text="Zaman Aralığı:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)
        timeframe_combo = ttk.Combobox(control_frame, textvariable=self.timeframe_var, values=list(TIMEFRAME_OPTIONS.keys()), state="readonly")
        timeframe_combo.grid(row=0, column=5, sticky=tk.W, padx=5, pady=5)

        self.analyze_button = ttk.Button(control_frame, text="Analiz Et", command=self._start_analysis)
        self.analyze_button.grid(row=0, column=6, padx=10, pady=5)

        self.export_button = ttk.Button(control_frame, text="CSV Dışa Aktar", command=self._export_csv, state=tk.DISABLED)
        self.export_button.grid(row=0, column=7, padx=10, pady=5)

        self.status_var = tk.StringVar(value="Hazır")
        status_label = ttk.Label(control_frame, textvariable=self.status_var, foreground="#006699")
        status_label.grid(row=1, column=0, columnspan=8, sticky=tk.W, padx=5)

        # Grafik alanı
        chart_frame = ttk.Frame(self.root)
        chart_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=chart_frame)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Özet alanı
        summary_frame = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        summary_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(summary_frame, text="Özet", font=("Helvetica", 12, "bold")).pack(anchor=tk.W)
        self.summary_text = scrolledtext.ScrolledText(summary_frame, height=10, state=tk.DISABLED)
        self.summary_text.pack(fill=tk.BOTH, expand=True, pady=5)

    # ------------------------------------------------------------------
    # Analiz süreci
    # ------------------------------------------------------------------
    def _start_analysis(self) -> None:
        if self._analysis_thread and self._analysis_thread.is_alive():
            messagebox.showinfo("Bilgi", "Devam eden bir analiz var. Lütfen bekleyin.")
            return

        coin_name = self.coin_var.get()
        timeframe_label = self.timeframe_var.get()
        vs_currency = self.currency_var.get().strip().lower()

        if coin_name not in POPULAR_COINS:
            messagebox.showerror("Hata", "Lütfen geçerli bir kripto para seçin.")
            return

        if timeframe_label not in TIMEFRAME_OPTIONS:
            messagebox.showerror("Hata", "Lütfen geçerli bir zaman aralığı seçin.")
            return

        if not vs_currency:
            messagebox.showerror("Hata", "Karşılık birimi boş olamaz.")
            return

        self._set_status("Veriler alınıyor...")
        self.analyze_button.config(state=tk.DISABLED)

        coin_id = POPULAR_COINS[coin_name]
        days = TIMEFRAME_OPTIONS[timeframe_label]

        def task() -> None:
            try:
                market_data = fetch_market_chart(coin_id, vs_currency, days)
            except CoinGeckoError as exc:
                self.root.after(0, lambda: self._handle_error(str(exc)))
                return
            except Exception as exc:  # pragma: no cover - beklenmeyen hatalar
                self.root.after(0, lambda: self._handle_error(f"Bilinmeyen hata: {exc}"))
                return

            self.root.after(0, lambda: self._process_market_data(market_data, coin_name, vs_currency))

        self._analysis_thread = threading.Thread(target=task, daemon=True)
        self._analysis_thread.start()

    def _process_market_data(self, market_data: MarketData, coin_name: str, vs_currency: str) -> None:
        prices = market_data.prices["price"].astype(float)
        enriched = enrich_with_indicators(prices)
        combined = enriched.join(market_data.volumes.rename(columns={"volume": "volume"}), how="left")
        summary = build_summary(prices)

        self._latest_data = combined
        self._draw_chart(combined, coin_name, vs_currency)
        self._update_summary(summary)

        self._set_status("Analiz tamamlandı")
        self.analyze_button.config(state=tk.NORMAL)
        self.export_button.config(state=tk.NORMAL)

    # ------------------------------------------------------------------
    # UI yardımcıları
    # ------------------------------------------------------------------
    def _draw_chart(self, data: pd.DataFrame, coin_name: str, vs_currency: str) -> None:
        self.figure.clear()

        ax_price = self.figure.add_subplot(211)
        ax_rsi = self.figure.add_subplot(212, sharex=ax_price)

        ax_price.plot(data.index, data["price"], label="Fiyat", color="#1f77b4")
        if "sma_20" in data:
            ax_price.plot(data.index, data["sma_20"], label="SMA 20", color="#ff7f0e")
        if "sma_50" in data:
            ax_price.plot(data.index, data["sma_50"], label="SMA 50", color="#2ca02c")
        if "ema_20" in data:
            ax_price.plot(data.index, data["ema_20"], label="EMA 20", color="#d62728")

        ax_price.set_title(f"{coin_name} fiyat trendi ({vs_currency.upper()})")
        ax_price.set_ylabel(f"Fiyat ({vs_currency.upper()})")
        ax_price.grid(True, alpha=0.3)
        ax_price.legend(loc="upper left")

        if "rsi_14" in data:
            ax_rsi.plot(data.index, data["rsi_14"], label="RSI 14", color="#9467bd")
            ax_rsi.axhline(70, color="red", linestyle="--", linewidth=1)
            ax_rsi.axhline(30, color="green", linestyle="--", linewidth=1)
            ax_rsi.set_ylabel("RSI")
            ax_rsi.set_ylim(0, 100)
            ax_rsi.grid(True, alpha=0.3)
            ax_rsi.legend(loc="upper left")

        self.figure.tight_layout()
        self.canvas.draw_idle()

    def _update_summary(self, summary: str) -> None:
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert(tk.END, summary)
        self.summary_text.config(state=tk.DISABLED)

    def _export_csv(self) -> None:
        if self._latest_data is None or self._latest_data.empty:
            messagebox.showinfo("Bilgi", "Önce analiz yapmalısınız.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Dosyası", "*.csv")],
            title="Analiz sonuçlarını kaydet",
        )
        if not file_path:
            return

        try:
            self._latest_data.to_csv(file_path, index_label="timestamp")
        except OSError as exc:
            messagebox.showerror("Hata", f"Dosya kaydedilemedi: {exc}")
            return

        messagebox.showinfo("Başarılı", "Dosya başarıyla kaydedildi.")

    def _handle_error(self, message: str) -> None:
        self._set_status("Hata oluştu")
        self.analyze_button.config(state=tk.NORMAL)
        messagebox.showerror("Hata", message)

    def _set_status(self, message: str) -> None:
        self.status_var.set(message)

    def run(self) -> None:
        self.root.mainloop()


def launch_app() -> None:
    root = tk.Tk()
    app = CryptoAnalyzerApp(root)
    app.run()


__all__ = ["CryptoAnalyzerApp", "launch_app"]
