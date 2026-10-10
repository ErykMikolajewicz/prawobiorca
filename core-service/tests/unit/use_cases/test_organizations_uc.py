import pytest

from src.app.dtos.organizations import NewOrganization, NewSuborganization, OrganizationData
from src.app.use_cases.organizations import (
    AddOrganization,
    AddSuborganization,
    DeleteOrganization,
    DeleteSuborganization,
    ListOrganizations,
    UpdateOrganization,
    UpdateSuborganization,
)
from src.domain.exceptions.organizations import OrganizationNotFound, SuborganizationNotFound

NEW_ORGANIZATION = NewOrganization(name="Politechnika Wrocławska", shortName="PWr")
NEW_SUBORGANIZATION = NewSuborganization(name="Wydział Mechaniczny")


async def test_list_organizations_success(
    mock_session_maker, mock_opened_session, mock_organizations_repo, uuid_generator
):
    organization = OrganizationData(
        id=next(uuid_generator), name="Politechnika Wrocławska", short_name="PWr", suborganizations=[]
    )
    mock_organizations_repo.list_all.return_value = [organization]

    use_case = ListOrganizations(session_maker=mock_session_maker, organizations_repo=mock_organizations_repo)
    result = await use_case.execute()

    assert result == [organization]
    mock_organizations_repo.list_all.assert_awaited_once_with(mock_opened_session)


async def test_add_organization_success(
    mock_session_maker, mock_opened_session, mock_organizations_repo, uuid_generator
):
    organization_id = next(uuid_generator)
    mock_organizations_repo.add.return_value = organization_id

    use_case = AddOrganization(session_maker=mock_session_maker, organizations_repo=mock_organizations_repo)
    result = await use_case.execute(NEW_ORGANIZATION)

    assert result == organization_id
    mock_organizations_repo.add.assert_awaited_once_with(mock_opened_session, NEW_ORGANIZATION)


async def test_update_organization_success(
    mock_session_maker, mock_opened_session, mock_organizations_repo, uuid_generator
):
    organization_id = next(uuid_generator)

    use_case = UpdateOrganization(session_maker=mock_session_maker, organizations_repo=mock_organizations_repo)
    await use_case.execute(organization_id, NEW_ORGANIZATION)

    mock_organizations_repo.update.assert_awaited_once_with(mock_opened_session, organization_id, NEW_ORGANIZATION)


async def test_update_organization_not_found(mock_session_maker, mock_organizations_repo, uuid_generator):
    mock_organizations_repo.update.side_effect = OrganizationNotFound()

    use_case = UpdateOrganization(session_maker=mock_session_maker, organizations_repo=mock_organizations_repo)

    with pytest.raises(OrganizationNotFound):
        await use_case.execute(next(uuid_generator), NEW_ORGANIZATION)


async def test_delete_organization_success(
    mock_session_maker, mock_opened_session, mock_organizations_repo, uuid_generator
):
    organization_id = next(uuid_generator)

    use_case = DeleteOrganization(session_maker=mock_session_maker, organizations_repo=mock_organizations_repo)
    await use_case.execute(organization_id)

    mock_organizations_repo.delete.assert_awaited_once_with(mock_opened_session, organization_id)


async def test_delete_organization_not_found(mock_session_maker, mock_organizations_repo, uuid_generator):
    mock_organizations_repo.delete.side_effect = OrganizationNotFound()

    use_case = DeleteOrganization(session_maker=mock_session_maker, organizations_repo=mock_organizations_repo)

    with pytest.raises(OrganizationNotFound):
        await use_case.execute(next(uuid_generator))


async def test_add_suborganization_success(
    mock_session_maker, mock_opened_session, mock_suborganizations_repo, uuid_generator
):
    organization_id = next(uuid_generator)
    suborganization_id = next(uuid_generator)
    mock_suborganizations_repo.add.return_value = suborganization_id

    use_case = AddSuborganization(session_maker=mock_session_maker, suborganizations_repo=mock_suborganizations_repo)
    result = await use_case.execute(organization_id, NEW_SUBORGANIZATION)

    assert result == suborganization_id
    mock_suborganizations_repo.add.assert_awaited_once_with(mock_opened_session, organization_id, NEW_SUBORGANIZATION)


async def test_add_suborganization_organization_not_found(
    mock_session_maker, mock_suborganizations_repo, uuid_generator
):
    mock_suborganizations_repo.add.side_effect = OrganizationNotFound()

    use_case = AddSuborganization(session_maker=mock_session_maker, suborganizations_repo=mock_suborganizations_repo)

    with pytest.raises(OrganizationNotFound):
        await use_case.execute(next(uuid_generator), NEW_SUBORGANIZATION)


async def test_update_suborganization_success(
    mock_session_maker, mock_opened_session, mock_suborganizations_repo, uuid_generator
):
    suborganization_id = next(uuid_generator)

    use_case = UpdateSuborganization(session_maker=mock_session_maker, suborganizations_repo=mock_suborganizations_repo)
    await use_case.execute(suborganization_id, NEW_SUBORGANIZATION)

    mock_suborganizations_repo.update.assert_awaited_once_with(
        mock_opened_session, suborganization_id, NEW_SUBORGANIZATION
    )


async def test_update_suborganization_not_found(mock_session_maker, mock_suborganizations_repo, uuid_generator):
    mock_suborganizations_repo.update.side_effect = SuborganizationNotFound()

    use_case = UpdateSuborganization(session_maker=mock_session_maker, suborganizations_repo=mock_suborganizations_repo)

    with pytest.raises(SuborganizationNotFound):
        await use_case.execute(next(uuid_generator), NEW_SUBORGANIZATION)


async def test_delete_suborganization_success(
    mock_session_maker, mock_opened_session, mock_suborganizations_repo, uuid_generator
):
    suborganization_id = next(uuid_generator)

    use_case = DeleteSuborganization(session_maker=mock_session_maker, suborganizations_repo=mock_suborganizations_repo)
    await use_case.execute(suborganization_id)

    mock_suborganizations_repo.delete.assert_awaited_once_with(mock_opened_session, suborganization_id)


async def test_delete_suborganization_not_found(mock_session_maker, mock_suborganizations_repo, uuid_generator):
    mock_suborganizations_repo.delete.side_effect = SuborganizationNotFound()

    use_case = DeleteSuborganization(session_maker=mock_session_maker, suborganizations_repo=mock_suborganizations_repo)

    with pytest.raises(SuborganizationNotFound):
        await use_case.execute(next(uuid_generator))
