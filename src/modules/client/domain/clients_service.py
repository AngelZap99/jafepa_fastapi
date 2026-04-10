# src/modules/clients/clients_service.py

from typing import List
from fastapi import HTTPException, status

from src.shared.models.client.client_model import Client
from src.modules.client.client_schema import ClientCreate, ClientUpdate
from src.modules.client.domain.clients_repository import ClientRepository


class ClientService:
    ####################
    # Private methods
    ####################
    def __init__(self, repository: ClientRepository) -> None:
        self.repository = repository

    def _ensure_email_not_taken(
        self, email: str | None, client_owner_id: int | None = None
    ) -> None:
        if not email:
            return
        existing = self.repository.get_by_email(email)

        # Si existe otro cliente con ese email → error
        if existing and (client_owner_id is None or existing.id != client_owner_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email {email} is already taken",
            )

    def _get_client_or_404(self, client_id: int) -> Client:
        client = self.repository.get(client_id)
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found",
            )
        return client

    ####################
    # Public methods
    ####################
    def list_clients(self, skip: int = 0, limit: int | None = None) -> List[Client]:
        return self.repository.list(skip=skip, limit=limit)

    def get_client(self, client_id: int) -> Client:
        return self._get_client_or_404(client_id)

    def create_client(self, payload: ClientCreate) -> Client:
        self._ensure_email_not_taken(payload.email)

        client = Client(
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            is_active=True,
        )

        return self.repository.add(client)

    def update_client(self, client_id: int, payload: ClientUpdate) -> Client:
        client = self._get_client_or_404(client_id)
        data = payload.model_dump(exclude_unset=True)

        # ¿Se actualiza el email?
        if "email" in data:
            self._ensure_email_not_taken(data["email"], client_owner_id=client.id)

        # Aplicar los cambios al modelo
        for field, value in data.items():
            setattr(client, field, value)

        return self.repository.update(client)

    def delete_client(self, client_id: int) -> Client:
        client = self._get_client_or_404(client_id)
        client.is_active = False
        self.repository.update(client)
        return client
