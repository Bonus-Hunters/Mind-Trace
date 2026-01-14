from core.config_loader import ConfigLoader, DatabaseConfigLoader

config = DatabaseConfigLoader()
print("Database Username:", config.get("POSTGRES_USER"))
