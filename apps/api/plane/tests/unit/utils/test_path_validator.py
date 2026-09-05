from urllib.parse import parse_qs, urlparse

from django.test import override_settings

from plane.utils.path_validator import get_safe_redirect_url


@override_settings(
    WEB_URL="http://localhost:8000",
    APP_BASE_URL="http://localhost:3000",
    ADMIN_BASE_URL="",
    SPACE_BASE_URL="",
)
def test_get_safe_redirect_url_encodes_invitation_query_parameters():
    invitation_path = "/workspace-invitations/?invitation_id=123&slug=test-workspace&token=invite-token"

    redirect_url = get_safe_redirect_url("http://localhost:3000", next_path=invitation_path)

    assert parse_qs(urlparse(redirect_url).query)["next_path"] == [invitation_path]
