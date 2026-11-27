from . import access, team_names, vehicles, team_brands, spgs, brands_targets, prices, locations, schedule, analytics, map, dashboard, records


ADMIN_PAGES = {
    'Master_Akses': access.render,
    'Master_Nama_Team': team_names.render,
    'Master_Plat': vehicles.render,
    'Master_Team': team_brands.render,
    'Master_SPG': spgs.render,
    'Master_Brand': brands_targets.render,
    'Master_Harga': prices.render,
    'Master_Lokasi': locations.render,
    'Master_Jadwal_Excel': schedule.render,
    'Analitik': analytics.render,
    'Peta_Rute': map.render,
    'Master_Laporan': records.render,
}


def render_admin_page(admin_view: str):
    ADMIN_PAGES.get(admin_view, dashboard.render)()
