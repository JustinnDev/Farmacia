import re

def extract_coords(url):
    """
    Extract latitude and longitude from a Google Maps URL.

    Args:
        url (str): The Google Maps URL containing coordinates.

    Returns:
        tuple: (latitude, longitude) as floats, or None if not found.
    """
    # Regex to match @lat,lng pattern
    match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
    if match:
        lat = float(match.group(1))
        lng = float(match.group(2))
        return lat, lng
    else:
        return None

if __name__ == "__main__":
    url = input("Enter Google Maps URL: ")
    coords = extract_coords(url)
    if coords:
        print(f"Latitude: {coords[0]}, Longitude: {coords[1]}")
    else:
        print("Coordinates not found in URL")