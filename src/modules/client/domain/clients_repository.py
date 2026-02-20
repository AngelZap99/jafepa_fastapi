# src/modules/clients/domain/clients_repository.py

from sqlalchemy.orm import Session
from src.shared.models.client.client_model import Client


class ClientRepository:

    def __init__(self, db: Session):
        self.db = db

    def list(self, skip: int = 0, limit: int | None = None):
        q = self.db.query(Client).offset(skip)
        if limit is not None:
            q = q.limit(limit)
        return q.all()

    def get(self, client_id: int) -> Client | None:
        return self.db.query(Client).filter(Client.id == client_id).first()

    def get_by_email(self, email: str) -> Client | None:
        return self.db.query(Client).filter(Client.email == email).first()

    def add(self, client: Client) -> Client:
        self.db.add(client)
        self.db.commit()
        self.db.refresh(client)
        return client

    def update(self, client: Client) -> Client:
        self.db.commit()
        self.db.refresh(client)
        return client
