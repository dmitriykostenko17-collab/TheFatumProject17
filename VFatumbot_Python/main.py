import asyncio
import os
import certifi
os.environ["SSL_CERT_FILE"] = certifi.where()

import flet as ft

import config
from bot_logic.core_logic import generate_ida, generate_random, PointResult
from bot_logic.card_factory import create_google_maps_url, create_google_maps_static_thumbnail
from storage.database import Database

# Initialize Database
db = Database(config.DATABASE_PATH)
db.create_tables()
user_profile = db.get_user()

# Fallback coordinates for UI
DEFAULT_LAT = 55.751244
DEFAULT_LON = 37.618423

def main(page: ft.Page):
    page.title = "TheFatumProject"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # Define State (Sync with database)
    state = {
        "lat": DEFAULT_LAT,
        "lon": DEFAULT_LON,
        "radius": config.DEFAULT_RADIUS,
        "filter_water": user_profile.is_include_water_points,
        "entropy_mode": "camera"
    }

    # UI Elements
    output_log = ft.Column(scroll=ft.ScrollMode.ALWAYS, expand=True)
    map_image = ft.Image(visible=False, width=300, height=200, fit=ft.ImageFit.CONTAIN)
    map_btn = ft.ElevatedButton("Open in Google Maps", icon=ft.Icons.MAP, visible=False)



    lat_field = ft.TextField(label="Latitude", value=str(state["lat"]), expand=1)
    lon_field = ft.TextField(label="Longitude", value=str(state["lon"]), expand=1)
    
    # Geolocator handler
    def on_geolocator_result(e):
        lat_field.value = str(e.latitude)
        lon_field.value = str(e.longitude)
        log(f"📍 GPS Location Updated: {e.latitude}, {e.longitude}", "green")
        update_settings(None)
        page.update()

    def on_geolocator_error(e):
        log(f"GPS Error: {e.error}", "red")

    geolocator = ft.Geolocator(
        on_position_change=None, # We use manual get_current_position
        on_error=on_geolocator_error
    )
    page.overlay.append(geolocator)

    async def get_gps_location(e):
        log("🛰 Requesting GPS location...", "blue")
        # In Flet, get_current_position is an async method
        try:
            pos = await geolocator.get_current_position_async()
            if pos:
                lat_field.value = str(pos.latitude)
                lon_field.value = str(pos.longitude)
                log(f"✅ GPS Position received: {pos.latitude}, {pos.longitude}", "green")
                update_settings(None)
        except Exception as ex:
            log(f"❌ GPS Failed: {ex}", "red")
        page.update()

    gps_btn = ft.IconButton(
        icon=ft.Icons.MY_LOCATION,
        tooltip="Get GPS Location",
        on_click=get_gps_location
    )

    rad_text = ft.Text(f"Radius: {state['radius']}m", size=16)
    rad_slider = ft.Slider(
        min=1000, max=20000, divisions=19, value=state["radius"],
        label="{value}m"
    )

    water_switch = ft.Switch(label="Filter Water Points", value=state["filter_water"])

    entropy_dropdown = ft.Dropdown(
        label="Entropy Source",
        value="camera",
        options=[
            ft.dropdown.Option("camera", "Camera (Local Quantum)"),
            ft.dropdown.Option("quantum", "Randonautica (Cloud Quantum)"),
            ft.dropdown.Option("pseudo", "Pseudo-Random (Testing)"),
        ],
        width=300
    )

    # Mobile UI Elements
    loading_ring = ft.ProgressRing(visible=False, width=40, height=40, stroke_width=4)
    snackbar = ft.SnackBar(ft.Text(""))
    page.overlay.append(snackbar)

    def log(message: str, color="white", show_snackbar=False):
        output_log.controls.append(ft.Text(message, color=color))
        if show_snackbar:
            snackbar.content.value = message
            snackbar.open = True
        page.update()

    # Camera Entropy Handler
    def on_file_result(e: ft.FilePickerResultEvent):
        if e.files:
            file_path = e.files[0].path
            log(f"--- Camera Entropy Captured ---", "yellow")
            from rngs.rng_wrapper import camera_rng_instance
            camera_rng_instance.feed_image(file_path)
            log(f"Quantum noise extracted from: {os.path.basename(file_path)}", "green", show_snackbar=True)
            page.update()

    file_picker = ft.FilePicker(on_result=on_file_result)
    page.overlay.append(file_picker)

    def update_settings(e):
        try:
            state["lat"] = float(lat_field.value)
            state["lon"] = float(lon_field.value)
        except:
            log("Invalid coordinates!", "red")
        
        state["radius"] = int(rad_slider.value)
        rad_text.value = f"Radius: {state['radius']}m"
        state["filter_water"] = water_switch.value
        state["entropy_mode"] = entropy_dropdown.value
        
        # Save to DB
        user_profile.is_include_water_points = state["filter_water"]
        db.save_user(user_profile)
        
        page.update()

    rad_slider.on_change = update_settings
    water_switch.on_change = update_settings
    entropy_dropdown.on_change = update_settings

    def handle_result(results, err):
        loading_ring.visible = False
        if err:
            log(f"Error: {err}", "red", show_snackbar=True)
            return

        if not results:
            log("No results returned.", "yellow", show_snackbar=True)
            return

        for r in results:
            log(f"✅ Success! {r.message}", "green")
            w3w = "(None)"
            if r.w3w and "words" in r.w3w:
                w3w = r.w3w["words"]
            log(f"W3W: ///{w3w}", "blue", show_snackbar=True)

            # Show map thumbnail
            map_url = create_google_maps_static_thumbnail([r.lat, r.lon])
            # Flet requires full valid URLs for Images. Google Maps API requires key.
            if config.GOOGLE_MAPS_API_KEY:
                map_image.src = map_url
                map_image.visible = True
            
            # Map button
            link = create_google_maps_url([r.lat, r.lon])
            map_btn.url = link
            map_btn.visible = True

        page.update()

    def run_coro(coro):
        """Helper to run async logic in Flet sync handlers"""
        loading_ring.visible = True
        page.update()

        try:
            # We can use asyncio.run if there is no loop
            import threading
            def runner():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                res, err = loop.run_until_complete(coro)
                page.run_thread(lambda: handle_result(res, err))
            threading.Thread(target=runner).start()
        except Exception as e:
            loading_ring.visible = False
            log(f"Execution Error: {e}", "red")

    def check_entropy() -> bool:
        if state["entropy_mode"] == "camera":
            from rngs.rng_wrapper import camera_rng_instance
            if not camera_rng_instance.entropy_pool:
                log("No camera entropy! Please click '📷 Capture' and take a dark photo first.", "red", show_snackbar=True)
                return False
        return True

    def click_attractor(e):
        if not check_entropy(): return
        log(f"\n--- Searching Attractor ({state['entropy_mode']}) ---", "yellow")
        update_settings(None)
        run_coro(generate_ida(state["lat"], state["lon"], state["radius"], "attractor", entropy_mode=state["entropy_mode"], filter_water=state["filter_water"]))

    def click_void(e):
        if not check_entropy(): return
        log(f"\n--- Searching Void ({state['entropy_mode']}) ---", "yellow")
        update_settings(None)
        run_coro(generate_ida(state["lat"], state["lon"], state["radius"], "void", entropy_mode=state["entropy_mode"], filter_water=state["filter_water"]))

    def click_anomaly(e):
        if not check_entropy(): return
        log(f"\n--- Searching Anomaly ({state['entropy_mode']}) ---", "yellow")
        update_settings(None)
        run_coro(generate_ida(state["lat"], state["lon"], state["radius"], "any", entropy_mode=state["entropy_mode"], filter_water=state["filter_water"]))

    def click_capture(e):
        log("--- Opening Camera/File Selection ---", "blue")
        file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE)

    def click_quantum(e):
        if not check_entropy(): return
        log(f"\n--- Generating Random Point ({state['entropy_mode']}) ---", "yellow")
        update_settings(None)
        run_coro(generate_random(state["lat"], state["lon"], state["radius"], entropy_mode=state["entropy_mode"], filter_water=state["filter_water"]))

    # Layout
    page.add(
        ft.Row([
            ft.Text("TheFatumProject", size=24, weight="bold"),
            loading_ring
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Divider(),
        
        ft.Text("📌 Location", size=20, weight="w500"),
        ft.Row([lat_field, lon_field, gps_btn]),
        
        ft.Divider(),
        ft.Text("⚙ Settings", size=20, weight="w500"),
        entropy_dropdown,
        rad_text,
        rad_slider,
        water_switch,

        ft.Divider(),
        ft.Text("🚀 Actions", size=20, weight="w500"),
        ft.Row([
            ft.ElevatedButton("Attractor", on_click=click_attractor, bgcolor=ft.Colors.RED_700, color=ft.Colors.WHITE),
            ft.ElevatedButton("Void", on_click=click_void, bgcolor=ft.Colors.BLUE_700, color=ft.Colors.WHITE),
            ft.ElevatedButton("Anomaly", on_click=click_anomaly, bgcolor=ft.Colors.PURPLE_700, color=ft.Colors.WHITE),
        ], alignment=ft.MainAxisAlignment.CENTER),
        
        ft.Row([
             ft.ElevatedButton("Capture (CamRNG)", on_click=click_capture, bgcolor=ft.Colors.GREEN_700, color=ft.Colors.WHITE),
             ft.ElevatedButton("Random Point", on_click=click_quantum, bgcolor=ft.Colors.TEAL_700, color=ft.Colors.WHITE),
        ], alignment=ft.MainAxisAlignment.CENTER),

        ft.Divider(),
        ft.Text("📋 Results", size=20, weight="w500"),
        
        ft.Row([
            ft.Container(content=output_log, expand=1, border=ft.border.all(1, ft.Colors.OUTLINE), padding=10, border_radius=10),
            ft.Column([map_image, map_btn], alignment=ft.MainAxisAlignment.START)
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.START, expand=True)
    )

if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.WEB_BROWSER, port=8557)


