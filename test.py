from sql import get_lastdata

data = get_lastdata()
print(f"Last Data: Suhu={data[1]}, Humidity={data[2]}, Lux={data[3]}, Timestamp={data[4]}")