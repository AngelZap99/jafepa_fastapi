# src/modules/clients/clients_router.py

from fastapi import APIRouter, Depends, status

from src.shared.database.dependencies import SessionDep

from src.modules.client.client_schema import (
    ClientCreate,
    ClientUpdate,
    ClientResponse,
)
from src.modules.client.domain.clients_service import ClientService
from src.modules.client.domain.clients_repository import ClientRepository

from src.modules.auth.auth_dependencies import get_current_user


router = APIRouter(
    prefix="/clients",
    tags=["clients"],
    dependencies=[Depends(get_current_user)],
)


def get_client_service(session: SessionDep) -> ClientService:
    client_repository = ClientRepository(session)
    return ClientService(client_repository)


@router.get(
    "/list",
    response_model=list[ClientResponse],
    status_code=status.HTTP_200_OK,
)
def list_clients(
    client_service: ClientService = Depends(get_client_service),
):
    return client_service.list_clients()


@router.get(
    "/{client_id:int}",
    response_model=ClientResponse,
    status_code=status.HTTP_200_OK,
)
def get_client(
    client_id: int,
    client_service: ClientService = Depends(get_client_service),
):
    return client_service.get_client(client_id)


@router.post(
    "/create",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_client(
    payload: ClientCreate,
    client_service: ClientService = Depends(get_client_service),
):
    return client_service.create_client(payload)


@router.put(
    "/update/{client_id}",
    response_model=ClientResponse,
    status_code=status.HTTP_200_OK,
)
def update_client(
    client_id: int,
    payload: ClientUpdate,
    client_service: ClientService = Depends(get_client_service),
):
    return client_service.update_client(client_id, payload)


@router.delete(
    "/delete/{client_id}",
    response_model=ClientResponse,
    status_code=status.HTTP_200_OK,
)
def delete_client(
    client_id: int,
    client_service: ClientService = Depends(get_client_service),
):
    return client_service.delete_client(client_id)
