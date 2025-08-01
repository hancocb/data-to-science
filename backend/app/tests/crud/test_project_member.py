import pytest
from pydantic import ValidationError
from sqlalchemy.exc import DataError
from sqlalchemy.orm import Session

from app import crud, models
from app.models.project_type import ProjectType
from app.schemas.project_member import ProjectMemberCreate, ProjectMemberUpdate
from app.schemas.role import Role
from app.tests.utils.project import create_project
from app.tests.utils.project_member import create_project_member
from app.tests.utils.team import create_team
from app.tests.utils.team_member import create_team_member
from app.tests.utils.user import create_user


def test_create_project_member(db: Session) -> None:
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    user = create_user(db)
    project_member = create_project_member(db, member_id=user.id, project_id=project.id)
    assert project_member
    assert user.id == project_member.member_id
    assert project.id == project_member.project_id
    assert project_member.project_type == ProjectType.PROJECT
    assert project_member.project_uuid == project.id
    assert project_member.role == Role.VIEWER  # default role


def test_create_project_members_with_different_roles(db: Session) -> None:
    project_owner = create_user(db)
    project_manager = create_user(db)
    project_viewer = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    manager_role = create_project_member(
        db, member_id=project_manager.id, project_id=project.id
    )
    crud.project_member.update_project_member(
        db, manager_role, ProjectMemberUpdate(role=Role.MANAGER)
    )
    viewer_role = create_project_member(
        db, member_id=project_viewer.id, project_id=project.id
    )
    owner_in_db = crud.project_member.get_by_project_and_member_id(
        db, project_uuid=project.id, member_id=project_owner.id
    )
    manager_in_db = crud.project_member.get(db, id=manager_role.id)
    viewer_in_db = crud.project_member.get(db, id=viewer_role.id)
    assert owner_in_db and manager_in_db and viewer_in_db
    assert owner_in_db.role == Role.OWNER
    assert manager_in_db.role == Role.MANAGER
    assert viewer_in_db.role == Role.VIEWER


def test_create_project_members(db: Session) -> None:
    project_owner = create_user(db)
    team = create_team(db, owner_id=project_owner.id)
    team_members = []
    for i in range(0, 5):
        team_member = create_team_member(db, team_id=team.id)
        team_members.append((team_member.member_id, Role.VIEWER))
    project = create_project(db, owner_id=project_owner.id, team_id=team.id)
    project_members = crud.project_member.create_multi_with_project(
        db, new_members=team_members, project_uuid=project.id
    )
    assert isinstance(project_members, list)
    assert len(project_members) == 6  # owner + five added project members


def test_get_project_member(db: Session) -> None:
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    owner_in_db = crud.project_member.get_by_project_and_member_id(
        db, member_id=owner.id, project_uuid=project.id
    )
    assert owner_in_db
    assert owner_in_db.member_id == owner.id
    assert owner_in_db.project_type == ProjectType.PROJECT
    assert owner_in_db.project_uuid == project.id
    assert owner_in_db.role == Role.OWNER


def test_get_list_of_project_members(db: Session) -> None:
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    member1 = create_project_member(db, project_id=project.id)
    member2 = create_project_member(db, project_id=project.id)
    project_members = crud.project_member.get_list_of_project_members(
        db, project_uuid=project.id
    )
    assert type(project_members) is list
    assert len(project_members) == 3  # owner + two added project members
    for project_member in project_members:
        assert (
            project.owner_id == project_member.member_id
            or member1.member_id == project_member.member_id
            or member2.member_id == project_member.member_id
        )
        assert project_member.project_type == ProjectType.PROJECT
        assert project_member.project_uuid == project.id
        assert (
            project_member.member_id == owner.id
            and project_member.role == Role.OWNER
            or project_member.member_id != owner.id
            and project_member.role == Role.VIEWER
        )
        assert project_member.full_name
        assert project_member.email


def test_get_list_of_project_members_with_specific_role(db: Session) -> None:
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    member1 = create_project_member(db, project_id=project.id)
    crud.project_member.update_project_member(
        db, member1, ProjectMemberUpdate(role=Role.MANAGER)
    )
    member2 = create_project_member(db, project_id=project.id)
    crud.project_member.update_project_member(
        db, member2, ProjectMemberUpdate(role=Role.MANAGER)
    )
    member3 = create_project_member(db, project_id=project.id)
    project_members = crud.project_member.get_list_of_project_members(
        db, project_uuid=project.id, role=Role.MANAGER
    )
    assert type(project_members) is list
    assert len(project_members) == 2
    for project_member in project_members:
        assert project_member.role == Role.MANAGER


def test_get_list_of_project_members_from_deactivated_project(db: Session) -> None:
    project = create_project(db)
    create_project_member(db, project_id=project.id)
    create_project_member(db, project_id=project.id)
    crud.project.deactivate(db, project_id=project.id, user_id=project.owner_id)
    project_members = crud.project_member.get_list_of_project_members(
        db, project_uuid=project.id
    )
    assert type(project_members) is list
    assert len(project_members) == 0


def test_update_project_member(db: Session) -> None:
    project_member = create_project_member(db)
    project_member_in_update = ProjectMemberUpdate(role=Role.MANAGER)
    project_member_update = crud.project_member.update_project_member(
        db,
        project_member_obj=project_member,
        project_member_in=project_member_in_update,
    )
    result = project_member_update.get("result")
    assert result
    assert result.id == project_member.id
    assert result.role == Role.MANAGER


def test_update_project_owner_member_role(db: Session) -> None:
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    project_member = crud.project_member.get_by_project_and_member_id(
        db, project_uuid=project.id, member_id=project_owner.id
    )
    assert project_member
    project_member_in_update = ProjectMemberUpdate(role=Role.MANAGER)
    project_member_update = crud.project_member.update_project_member(
        db,
        project_member_obj=project_member,
        project_member_in=project_member_in_update,
    )
    assert project_member_update["result"] is None


def test_update_role_for_only_project_owner(db: Session) -> None:
    owner = create_user(db)
    project = create_project(db, owner_id=owner.id)
    project_owner = crud.project_member.get_by_project_and_member_id(
        db, project_uuid=project.id, member_id=owner.id
    )
    assert project_owner
    project_owner_in_update = ProjectMemberUpdate(role=Role.MANAGER)
    project_owner_update = crud.project_member.update_project_member(
        db, project_member_obj=project_owner, project_member_in=project_owner_in_update
    )
    assert project_owner_update["result"] is None


def test_delete_project_member(db: Session) -> None:
    project_member = create_project_member(db)
    project_member2 = crud.project_member.remove(db, id=project_member.id)
    project_member3 = crud.project_member.get(db, id=project_member.id)
    assert project_member3 is None
    assert project_member2
    assert project_member2.id == project_member.id
    assert project_member2.role == project_member.role
    assert project_member2.member_id == project_member.member_id


def test_delete_project_members(db: Session) -> None:
    project_owner = create_user(db)
    team = create_team(db, owner_id=project_owner.id)
    project = create_project(db, team_id=team.id, owner_id=project_owner.id)
    other_project = create_project(db, team_id=team.id, owner_id=project_owner.id)
    for i in range(0, 5):
        create_project_member(db, project_id=project.id)
        create_project_member(db, project_id=other_project.id)
    removed_project_members = crud.project_member.delete_multi(
        db, project_uuid=project.id, team_id=team.id
    )
    assert isinstance(removed_project_members, list)
    assert len(removed_project_members) == 5
    for project_member in removed_project_members:
        assert crud.project_member.get(db, id=project_member.id) is None


def test_assign_project_member_invalid_role(db: Session) -> None:
    with pytest.raises(DataError):
        create_project_member(db, role="invalid-role")  # type: ignore


def test_assign_project_member_invalid_project_type(db: Session) -> None:
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    user = create_user(db)

    # Test creating project member with invalid project_type
    with pytest.raises(DataError):
        crud.project_member.create_with_project(
            db,
            obj_in=ProjectMemberCreate(member_id=user.id),
            project_id=project.id,
            project_type="INVALID_TYPE",  # type: ignore
        )


def test_project_member_target_project_property(db: Session) -> None:
    project_owner = create_user(db)
    project = create_project(db, owner_id=project_owner.id)
    user = create_user(db)
    project_member = create_project_member(db, member_id=user.id, project_id=project.id)

    # Get the project_member from the database within a session context
    with db as session:
        project_member_in_session = session.get(models.ProjectMember, project_member.id)
        assert project_member_in_session is not None

        # Test that target_project property returns the correct project
        target_project = project_member_in_session.target_project
        assert target_project is not None
        assert target_project.id == project.id
        assert target_project.title == project.title
