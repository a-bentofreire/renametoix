# encoding=utf-8
# -*- coding: UTF-8 -*-

# ------------------------------------------------------------------------
# Copyright (c) 2024-2025 Alexandre Bento Freire. All rights reserved.
# Licensed under the GPLv3 License.
# ------------------------------------------------------------------------

# cSpell:ignoreRegExp (geocoders|Nominatim|piexif|geolocator|geoapi)
from geopy.geocoders import Nominatim
import piexif


class GeoWorker:
    def __init__(self) -> None:
        self.files = {}

    def is_slow(self):
        return True

    def get_extensions(self):
        return ['.jpg', '.jpeg']

    def eval_expr(self, macro, filename, groups):
        fields = self.files[filename]
        if fields:
            result = macro
            for key in fields.keys():
                result = result.replace(f"%{key}%", str(fields[key] or ""))
            return result.rstrip(",; ")
        raise

    def prepare(self, files):
        for filename in files:
            lat, lng = self._get_gps_from_image(filename)
            self.files[filename] = self._get_location_details(lat, lng) if lat else None

    def _get_location_details(self, latitude, longitude):
        geolocator = Nominatim(user_agent="geoapi")
        coordinates = f"{latitude}, {longitude}"
        location = geolocator.reverse(coordinates, language="en")

        if location and location.raw.get('address'):
            address = location.raw['address']
            return {
                'country': address.get('country'),
                'state': address.get('state'),
                'city': address.get('city') or address.get('town') or address.get('village'),
                'postcode': address.get('postcode'),
                'suburb': address.get('suburb')
            }
        return None

    def _get_gps_from_image(self, filename):
        try:
            gps_info = (piexif.load(filename) or {}).get("GPS")

            def calc_coord(index):
                values = gps_info.get(index + 1)
                ref = gps_info.get(index)
                if not values or not ref:
                    return None
                decimal = (values[0][0] / values[0][1]) + ((values[1][0] / values[1][1]) / 60.0) \
                    + (values[2][0] / values[2][1] / 3600.0)
                return -decimal if ref in [b'S', b'W'] else decimal

            return (calc_coord(1), calc_coord(3)) if gps_info else (None, None)
        except:
            return None, None


def get_worker():
    return GeoWorker()
