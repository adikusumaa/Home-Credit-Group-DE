import pandas as pd
import glob
import os

folder_parquet = r"D:\Academic-Project\Portofolio Data Engineer HomeCredit Group\hasil_download_gold"

nama_csv_output = "hasil_gold_all_data.csv"

df = pd.read_parquet(folder_parquet)

print(f"✅ Berhasil membaca data! Jumlah baris: {len(df)}, Jumlah kolom: {len(df.columns)}")

df.to_csv(nama_csv_output, index=False, encoding='utf-8')

print(f"🎉 Selesai! File CSV tersimpan di: {os.path.abspath(nama_csv_output)}")