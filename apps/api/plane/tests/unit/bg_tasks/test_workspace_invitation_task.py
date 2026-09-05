from unittest.mock import Mock
from urllib.parse import parse_qs, urlparse

import pytest

from plane.bgtasks import workspace_invitation_task
from plane.db.models import WorkspaceMemberInvite


@pytest.mark.django_db
def test_workspace_invitation_links_to_prefilled_magic_code_form(workspace, monkeypatch):
    invitee_email = "invitee@plane.so"
    invite_token = "workspace-invite-token"
    invitation = WorkspaceMemberInvite.objects.create(
        workspace=workspace,
        email=invitee_email,
        token=invite_token,
        created_by=workspace.owner,
    )

    magic_code_provider = Mock()
    magic_code_provider.return_value.initiate.return_value = ("magic_invitee@plane.so", "123456")
    monkeypatch.setattr(workspace_invitation_task, "MagicCodeProvider", magic_code_provider)
    monkeypatch.setattr(
        workspace_invitation_task,
        "get_email_configuration",
        Mock(return_value=("smtp.example.com", "user", "password", "587", "1", "0", "from@example.com")),
    )
    monkeypatch.setattr(workspace_invitation_task, "render_to_string", Mock(return_value="<p>Invitation</p>"))
    monkeypatch.setattr(workspace_invitation_task, "get_connection", Mock())

    email_message = Mock()
    monkeypatch.setattr(workspace_invitation_task, "EmailMultiAlternatives", Mock(return_value=email_message))

    workspace_invitation_task.workspace_invitation(
        invitee_email,
        workspace.id,
        invite_token,
        "http://localhost:3000",
        workspace.owner.email,
    )

    magic_code_provider.assert_called_once_with(request=None, key=invitee_email)
    rendered_context = workspace_invitation_task.render_to_string.call_args.args[1]
    invitation_url = urlparse(rendered_context["abs_url"])
    query = parse_qs(invitation_url.query)

    assert invitation_url.path == "/sign-up"
    assert query["email"] == [invitee_email]
    assert query["invitation_id"] == [str(invitation.id)]
    assert query["slug"] == [workspace.slug]
    assert query["next_path"] == [
        f"/workspace-invitations/?invitation_id={invitation.id}&slug={workspace.slug}&token={invite_token}"
    ]
    assert invitation_url.fragment == "code=123456"
