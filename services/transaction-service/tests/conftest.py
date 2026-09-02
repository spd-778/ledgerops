import os

os.environ["DATABASE_URL"] = (
    "postgresql+psycopg2://ledgerops:ledgerops_dev_password@localhost:5432/ledgerops"
)
