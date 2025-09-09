
import sys
import traceback
import time

import pynmea2
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D   

# to make the code work withactual hardware too
try: 
    import serial
except Exception:
    serial = None


USE_SERIAL = False         # True -> read from a real/virtual COM port; False -> use built-in test data
PORT = "COM5"              # change to your simulator COM port (Windows e.g. "COM5")/ it might be com7
BAUD = 9600
MAX_POINTS = 300           


# storage lists 
time_data = []
lat_data = []
lon_data = []
alt_data = []

def parse_nmea(line):
    
    try:
        msg = pynmea2.parse(line)
    except Exception:
        return None

    # Accept GGA sentence types that contain altitude
    if msg.sentence_type in ("GGA", "GNGGA", "GPGGA"):
        # timestamp may be a datetime.time object
        ts = getattr(msg, "timestamp", None)
        if ts is not None:
            try:
                time_str = f"{ts.hour:02d}:{ts.minute:02d}:{ts.second:02d}"
            except Exception:
                time_str = str(ts)
        else:
            time_str = ""

        
        try:
            lat = float(msg.latitude) if msg.latitude not in (None, "") else None
            lon = float(msg.longitude) if msg.longitude not in (None, "") else None
            alt = float(msg.altitude) if getattr(msg, "altitude", None) not in (None, "") else None
        except Exception:
            return None

        if lat is None or lon is None or alt is None:
            return None

        return time_str, lat, lon, alt

    return None


def collect_from_serial(port=PORT, baud=BAUD, max_points=MAX_POINTS):
    if serial is None:
        print("[!] pyserial not available. Install it with: pip install pyserial")
        return

    try:
        ser = serial.Serial(port, baud, timeout=1)
    except Exception as e:
        print(f"[!] Could not open serial port {port}: {e}")
        return

    print(f"[i] Listening on {port} @ {baud} baud. Collecting up to {max_points} points... (Ctrl+C to stop)")

    try:
        while len(lat_data) < max_points:
            raw = ser.readline().decode("ascii", errors="ignore").strip()
            if not raw:
                continue
            parsed = parse_nmea(raw)
            if parsed:
                t, la, lo, al = parsed
                time_data.append(t)
                lat_data.append(la)
                lon_data.append(lo)
                alt_data.append(al)
                print(f"{len(lat_data):03d} | {t} | {la:.6f}, {lo:.6f} | {al:.2f} m")
    except KeyboardInterrupt:
        print("\n[i] Interrupted by user.")
    except Exception:
        print("[!] Unexpected error while reading serial:")
        traceback.print_exc()
    finally:
        ser.close()
        print("[i] Serial closed.")


def collect_from_testlines():
    "test gga sentenses"
    test_lines = [
        "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47",
        "$GPGGA,123520,4807.123,N,01131.321,E,1,08,0.9,550.0,M,46.9,M,,*48",
        "$GPGGA,123521,4807.210,N,01131.600,E,1,08,0.9,560.0,M,46.9,M,,*49",
        "$GPGGA,123522,4807.350,N,01131.800,E,1,08,0.9,570.0,M,46.9,M,,*50",
        "$GPGGA,123523,4807.500,N,01132.050,E,1,08,0.9,580.0,M,46.9,M,,*51",
        "$GPGGA,123524,4807.720,N,01132.300,E,1,08,0.9,590.0,M,46.9,M,,*52"
    ]
    for line in test_lines:
        parsed = parse_nmea(line)
        if parsed:
            t, la, lo, al = parsed
            time_data.append(t)
            lat_data.append(la)
            lon_data.append(lo)
            alt_data.append(al)

def plot_3d(save_png=False):
    """Plot the collected latitude, longitude and altitude in 3D."""
    try:
        if not lat_data:
            print("[!] No data collected. Nothing to plot.")
            return

        fig = plt.figure(figsize=(9, 6))
        ax = fig.add_subplot(111, projection="3d")   
        # Plot the line and points
        ax.plot(lon_data, lat_data, alt_data, marker="o", linestyle="-", linewidth=1.5)
        ax.scatter([lon_data[0]], [lat_data[0]], [alt_data[0]], color="green", s=60, label="Start")
        ax.scatter([lon_data[-1]], [lat_data[-1]], [alt_data[-1]], color="red", s=60, label="End")

        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_zlabel("Altitude (m)")
        ax.set_title("3D GNSS Trajectory")
        ax.legend()
        plt.tight_layout()

        if save_png:
            outname = "trajectory_3d.png"
            plt.savefig(outname, dpi=200)
            print(f"[i] Saved {outname}")

        plt.show()
    except NameError as ne:
        print("[!] NameError in plot_3d():", ne)
        traceback.print_exc()
    except Exception:
        print("[!] Unexpected error in plot_3d():")
        traceback.print_exc()



if __name__ == "__main__":
    # Clear globals (useful if re-running interactively)
    time_data.clear(); lat_data.clear(); lon_data.clear(); alt_data.clear()

    if USE_SERIAL:
        collect_from_serial()
    else:
        collect_from_testlines()

    # final sanity print
    print(f"[i] Collected {len(lat_data)} points.")
    for i in range(len(lat_data)):
        print(f"{i+1:03d}: {time_data[i]} | {lat_data[i]:.6f} , {lon_data[i]:.6f} | {alt_data[i]:.2f}m")

    plot_3d(save_png=True)
