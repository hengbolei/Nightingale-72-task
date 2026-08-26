from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    app_name: str = "Nightingale Care Note"
    environment: str = "development"


settings = Settings()
