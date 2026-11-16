from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from core_service.application.dtos.account import RegistrationData
from core_service.application.use_cases.account import CreateAccount
from core_service.domain.exceptions.users import UserExists
from core_service.framework.dependencies.accounts import get_create_account
from core_service.framework.dependencies.client_address import get_client_ip

account_router = APIRouter(tags=["account"], prefix="/api")


@account_router.post(
    "/accounts/register",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_409_CONFLICT: {"description": "User with that login already exists."},
        status.HTTP_429_TOO_MANY_REQUESTS: {"description": "Too many registration attempts!"},
    },
)
async def create_account(
    registration_data: RegistrationData,
    create_account_: Annotated[CreateAccount, Depends(get_create_account)],
    ip_address: Annotated[str, Depends(get_client_ip)],
):

    try:
        await create_account_.execute(registration_data, ip_address)
    except UserExists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with that login already exists.")
