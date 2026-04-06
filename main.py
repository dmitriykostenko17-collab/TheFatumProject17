import asyncio
import os
import certifi
import traceback
from datetime import datetime
os.environ["SSL_CERT_FILE"] = certifi.where()

import flet as ft

import config
from bot_logic.core_logic import generate_ida, generate_random
from bot_logic.card_factory import create_google_maps_url
from storage.database import Database

# --- ANDROID LOGGING ---
LOG_PATH = os.path.join(config.WRITABLE_DIR, "fatum_log.txt")
def log_trace(msg):
    try:
        with open(LOG_PATH, "a") as f:
            f.write(f"{datetime.now().isoformat()}: {msg}\n")
    except: pass

async def main(page: ft.Page):
    # CRITICAL: SET BG FIRST
    page.bgcolor = "#0E1621"
    page.title = "Fatum Bot"
    page.padding = 0

    try:
        log_trace("ENTRY")
        
        # Colors
        TG_BG = "#0E1621"
        TG_HEADER = "#17212B"
        TG_BOT_BUBBLE = "#182533"
        TG_ACCENT = "#2B5278"
        ACCENT_COLOR = "#1C2A39" 
        TG_TEXT = "#FFFFFF"

        # --- DB ---
        try:
            db = Database(config.DATABASE_PATH)
            db.create_tables()
            u_prof = db.get_user()
        except:
            class Dummy: is_include_water_points = False
            u_prof = Dummy()

        # --- FONTS ---
        page.fonts = {
            "Geomanist": "fonts/Geomanist-Regular.ttf",
            "Geomanist-Bold": "fonts/Geomanist-Medium.ttf"
        }
        page.theme = ft.Theme(font_family="Geomanist")

        state = {
            "lat": 55.751244, "lon": 37.618423,
            "radius": config.DEFAULT_RADIUS,
            "filter_water": u_prof.is_include_water_points,
            "entropy": "camera", 
        }

        chat = ft.ListView(expand=True, spacing=10, padding=20)

        def create_bubble(txt, bot=True):
            if bot:
                return ft.Row([
                    ft.Container(ft.Image(src="logo.png", width=35, height=35, border_radius=17), alignment=ft.alignment.bottom_left),
                    ft.Container(ft.Text(txt, color=TG_TEXT), bgcolor=TG_BOT_BUBBLE, padding=12, border_radius=ft.border_radius.only(top_left=15, top_right=15, bottom_right=15, bottom_left=2), width=280)
                ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.END)
            else:
                return ft.Row([
                    ft.Container(ft.Text(txt, color=TG_TEXT), bgcolor=TG_ACCENT, padding=12, border_radius=ft.border_radius.only(top_left=15, top_right=15, bottom_left=15, bottom_right=2), width=280)
                ], alignment=ft.MainAxisAlignment.END)

        async def msg(t):
            chat.controls.append(create_bubble("...", True))
            page.update()
            await asyncio.sleep(0.5)
            chat.controls.pop()
            chat.controls.append(create_bubble(t, True))
            page.update()
            chat.scroll_to(offset=-1, duration=300)

        async def run_scan(m, rnd=False):
            lbl = "КВАНТОВАЯ ТОЧКА" if rnd else m.upper()
            chat.controls.append(create_bubble(lbl, False))
            page.update()
            await msg(f"Поиск {lbl} (Источник: {state['entropy'].upper()})...")
            try:
                if rnd: c = generate_random(state["lat"], state["lon"], state["radius"], state["entropy"], state["filter_water"])
                else: c = generate_ida(state["lat"], state["lon"], state["radius"], m, state["entropy"], state["filter_water"])
                res, err = await c
                if err: await msg(f"Ошибка: {err}")
                elif res:
                    r = res[0]
                    t = f"✅ Координаты: {r.lat:.6f}, {r.lon:.6f}"
                    await msg(t)
                    chat.controls.append(ft.ElevatedButton("Google Maps", icon="map", bgcolor=ACCENT_COLOR, color="white", on_click=lambda _: page.launch_url(create_google_maps_url([r.lat, r.lon]))))
                else: await msg("Ничего не найдено.")
            except Exception as e: await msg(f"Ошибка: {e}")
            page.update()

        async def sync_loc(e):
            await msg("Синхронизация GPS...")
            await asyncio.sleep(1)
            state["lat"], state["lon"] = 55.7539, 37.6208
            await msg(f"📍 {state['lat']}, {state['lon']}")

        async def toggle_e(e):
            state["entropy"] = "quantum" if state["entropy"] == "camera" else "camera"
            e_btn.text = f"ИСТОЧНИК: {state['entropy'].upper()}"
            await msg(f"Источник изменен на: {state['entropy'].upper()}")
            page.update()

        # --- KEYBOARD ---
        e_btn = ft.ElevatedButton(f"ИСТОЧНИК: {state['entropy'].upper()}", bgcolor=ACCENT_COLOR, color="white", on_click=toggle_e, expand=True)
        
        kb = ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.ElevatedButton("АТТРАКТОР", bgcolor=ACCENT_COLOR, color="white", expand=True, on_click=lambda _: asyncio.create_task(run_scan("attractor"))),
                    ft.ElevatedButton("ПУСТОТА", bgcolor=ACCENT_COLOR, color="white", expand=True, on_click=lambda _: asyncio.create_task(run_scan("void"))),
                    ft.ElevatedButton("АНОМАЛИЯ", bgcolor=ACCENT_COLOR, color="white", expand=True, on_click=lambda _: asyncio.create_task(run_scan("any")))
                ], spacing=5),
                ft.Row([
                    ft.ElevatedButton("КВАНТОВАЯ ТОЧКА", bgcolor=ACCENT_COLOR, color="white", expand=True, on_click=lambda _: asyncio.create_task(run_scan("random", True))),
                    ft.ElevatedButton("Местоположение", bgcolor=ACCENT_COLOR, color="white", expand=True, on_click=sync_loc),
                ], spacing=5),
                ft.Row([e_btn])
            ]), padding=10, bgcolor=TG_HEADER
        )

        header = ft.Container(
            content=ft.Row([
                ft.Image(src="logo.png", width=30, height=30),
                ft.Column([ft.Text("Fatum Bot", weight="bold"), ft.Text("онлайн", size=12, color="#708499")], spacing=0)
            ]), padding=10, bgcolor=TG_HEADER
        )

        page.clean()
        page.add(ft.Column([header, chat, kb], expand=True, spacing=0))
        page.update()
        log_trace("RENDER OK")
        await msg("Система готова. Выберите действие.")

    except Exception as e:
        log_trace(f"ERROR: {traceback.format_exc()}")
        page.add(ft.Text(f"CRITICAL: {e}", color="red"))
        page.update()

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8557, assets_dir="assets")
