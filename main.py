import requests
from statistics import mean
from sqlalchemy import create_engine, Column, Integer, Float
from sqlalchemy.orm import declarative_base, sessionmaker


Base = declarative_base()


class WeatherRecord(Base):
    __tablename__ = "weather_records"

    id = Column(Integer, primary_key=True)
    latitude = Column(Float)
    longitude = Column(Float)
    month = Column(Integer)
    day = Column(Integer)
    year = Column(Integer)

    avg_temperature = Column(Float)
    min_temperature = Column(Float)
    max_temperature = Column(Float)

    avg_wind_speed = Column(Float)
    min_wind_speed = Column(Float)
    max_wind_speed = Column(Float)

    sum_precipitation = Column(Float)
    min_precipitation = Column(Float)
    max_precipitation = Column(Float)


class WeatherData:
    def __init__(self, latitude, longitude, month, day, years):
        self.latitude = latitude
        self.longitude = longitude
        self.month = month
        self.day = day
        self.years = years

        self.temperatures = []
        self.wind_speeds = []
        self.precipitations = []

    def get_weather_for_year(self, year):
        date = f"{year}-{self.month:02d}-{self.day:02d}"

        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "start_date": date,
            "end_date": date,
            "daily": "temperature_2m_mean,wind_speed_10m_max,precipitation_sum",
            "temperature_unit": "fahrenheit",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "timezone": "America/Chicago"
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()["daily"]

        temperature = data["temperature_2m_mean"][0]
        wind_speed = data["wind_speed_10m_max"][0]
        precipitation = data["precipitation_sum"][0]

        return temperature, wind_speed, precipitation

    def collect_five_year_data(self):
        for year in self.years:
            temperature, wind_speed, precipitation = self.get_weather_for_year(year)
            self.temperatures.append(temperature)
            self.wind_speeds.append(wind_speed)
            self.precipitations.append(precipitation)

    def get_temperature_stats(self):
        return mean(self.temperatures), min(self.temperatures), max(self.temperatures)

    def get_wind_speed_stats(self):
        return mean(self.wind_speeds), min(self.wind_speeds), max(self.wind_speeds)

    def get_precipitation_stats(self):
        return sum(self.precipitations), min(self.precipitations), max(self.precipitations)


class WeatherDatabase:
    def __init__(self, database_url="sqlite:///weather.db"):
        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def save_weather_record(self, weather_data):
        avg_temp, min_temp, max_temp = weather_data.get_temperature_stats()
        avg_wind, min_wind, max_wind = weather_data.get_wind_speed_stats()
        sum_precip, min_precip, max_precip = weather_data.get_precipitation_stats()

        record = WeatherRecord(
            latitude=weather_data.latitude,
            longitude=weather_data.longitude,
            month=weather_data.month,
            day=weather_data.day,
            year=max(weather_data.years),

            avg_temperature=avg_temp,
            min_temperature=min_temp,
            max_temperature=max_temp,

            avg_wind_speed=avg_wind,
            min_wind_speed=min_wind,
            max_wind_speed=max_wind,

            sum_precipitation=sum_precip,
            min_precipitation=min_precip,
            max_precipitation=max_precip
        )

        self.session.add(record)
        self.session.commit()

    def get_all_records(self):
        return self.session.query(WeatherRecord).all()


def display_records(records):
    for record in records:
        print("\nAustin, Texas Weather Summary")
        print("--------------------------------")
        print(f"Latitude: {record.latitude}")
        print(f"Longitude: {record.longitude}")
        print(f"Date analyzed: {record.month}/{record.day}")
        print(f"Most recent year stored: {record.year}")
        print(f"Five-year average temperature: {record.avg_temperature:.2f} °F")
        print(f"Five-year minimum temperature: {record.min_temperature:.2f} °F")
        print(f"Five-year maximum temperature: {record.max_temperature:.2f} °F")
        print(f"Five-year average wind speed: {record.avg_wind_speed:.2f} mph")
        print(f"Five-year minimum wind speed: {record.min_wind_speed:.2f} mph")
        print(f"Five-year maximum wind speed: {record.max_wind_speed:.2f} mph")
        print(f"Five-year total precipitation: {record.sum_precipitation:.2f} inches")
        print(f"Five-year minimum precipitation: {record.min_precipitation:.2f} inches")
        print(f"Five-year maximum precipitation: {record.max_precipitation:.2f} inches")


def main():
    years = [2021, 2022, 2023, 2024, 2025]

    weather_data = WeatherData(
        latitude=30.2672,
        longitude=-97.7431,
        month=7,
        day=13,
        years=years
    )

    weather_data.collect_five_year_data()

    database = WeatherDatabase()
    database.save_weather_record(weather_data)

    records = database.get_all_records()
    display_records(records)


if __name__ == "__main__":
    main()
