#!/usr/bin/env python3
"""
Script de préchargement des émojis animés Google Noto.
Télécharge tous les GIFs et crée l'index emoji_index.json.

Usage:
    python download_emojis.py
"""
import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

API_URL = "https://googlefonts.github.io/noto-emoji-animation/data/api.json"
GIF_URL_PATTERN = "https://fonts.gstatic.com/s/e/notoemoji/latest/{codepoint}/512.gif"


def download_all_emojis(output_dir: str):
    """Télécharge tous les émojis et crée l'index"""
    emojis_dir = os.path.join(output_dir, "emojis")
    os.makedirs(emojis_dir, exist_ok=True)

    # Récupérer l'index depuis l'API
    print("Fetching emoji index from Google Noto API...")
    response = requests.get(API_URL, timeout=30)
    response.raise_for_status()
    data = response.json()

    # Créer l'index local
    emoji_index = []
    for icon in data["icons"]:
        codepoint = icon["codepoint"]
        tags = icon.get("tags", [])
        name = tags[0].strip(":") if tags else codepoint
        category = icon.get("categories", ["Other"])[0]

        emoji_index.append({
            "codepoint": codepoint,
            "name": name,
            "tags": tags,
            "category": category
        })

    # Sauvegarder l'index
    index_path = os.path.join(output_dir, "emoji_index.json")
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(emoji_index, f, indent=2, ensure_ascii=False)
    print(f"Index saved: {len(emoji_index)} emojis")

    # Télécharger les GIFs en parallèle
    def download_gif(emoji):
        codepoint = emoji["codepoint"]
        gif_path = os.path.join(emojis_dir, f"{codepoint}.gif")
        if os.path.exists(gif_path):
            return codepoint, True, "cached"

        url = GIF_URL_PATTERN.format(codepoint=codepoint)
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            with open(gif_path, "wb") as f:
                f.write(r.content)
            return codepoint, True, "downloaded"
        except Exception as e:
            return codepoint, False, str(e)

    print(f"Downloading {len(emoji_index)} GIFs...")
    downloaded = 0
    cached = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(download_gif, e): e for e in emoji_index}
        done = 0
        for future in as_completed(futures):
            done += 1
            codepoint, success, status = future.result()
            if success:
                if status == "cached":
                    cached += 1
                else:
                    downloaded += 1
            else:
                failed += 1
                print(f"  Failed: {codepoint} - {status}")

            if done % 50 == 0:
                print(f"Progress: {done}/{len(emoji_index)}")

    print(f"\nDownload complete!")
    print(f"  Downloaded: {downloaded}")
    print(f"  Cached: {cached}")
    print(f"  Failed: {failed}")


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    assets_dir = os.path.join(script_dir, "assets")
    download_all_emojis(assets_dir)
