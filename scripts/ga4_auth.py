"""
One-time OAuth setup for GA4 + GSC APIs.
Run this once to generate a token.
"""
import json
import os
from google_auth_oauthlib.flow import InstalledAppFlow
from google.analytics.admin_v1alpha import AnalyticsAdminServiceClient

SCOPES = [
    'https://www.googleapis.com/auth/analytics.readonly',
    'https://www.googleapis.com/auth/analytics.edit',  # added 23 Jun 2026 — lets us CREATE GA4 properties + data streams for the ~9 fleet sites that have none
    'https://www.googleapis.com/auth/analytics.manage.users.readonly',
    'https://www.googleapis.com/auth/webmasters.readonly',
    'https://www.googleapis.com/auth/indexing',
]

CLIENT_SECRET = os.path.expanduser(
    '~/Downloads/client_secret_570249470362-thrbb8uo285crbgc0lu2ouq7hud09j5s.apps.googleusercontent.com.json'
)
TOKEN_FILE = os.path.expanduser('~/rank4ai-dashboard/scripts/ga4_token.json')


def _client_config():
    """Prefer the downloaded client_secret file; fall back to the client_id/secret
    already embedded in ga4_token.json (the Downloads file went missing 23 Jun)."""
    if os.path.exists(CLIENT_SECRET):
        return None  # signal: use from_client_secrets_file
    tok = json.load(open(TOKEN_FILE))
    return {
        "installed": {
            "client_id": tok["client_id"],
            "client_secret": tok["client_secret"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }


def main():
    cfg = _client_config()
    if cfg is None:
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET, SCOPES)
    else:
        flow = InstalledAppFlow.from_client_config(cfg, SCOPES)
    creds = flow.run_local_server(port=0)

    # Save token
    token_data = {
        'token': creds.token,
        'refresh_token': creds.refresh_token,
        'token_uri': creds.token_uri,
        'client_id': creds.client_id,
        'client_secret': creds.client_secret,
        'scopes': list(creds.scopes) if creds.scopes else [],
    }
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f, indent=2)
    print(f'Token saved to {TOKEN_FILE}')

    # List available GA4 properties
    print('\nListing GA4 properties you have access to:\n')
    try:
        admin_client = AnalyticsAdminServiceClient(credentials=creds)
        accounts = admin_client.list_account_summaries()
        for account in accounts:
            print(f'Account: {account.display_name} ({account.name})')
            for prop in account.property_summaries:
                print(f'  Property: {prop.display_name}')
                print(f'  Property ID: {prop.property.split("/")[-1]}')
                print()
    except Exception as e:
        print(f'Could not list properties: {e}')
        print('\nYou can find your property ID at:')
        print('analytics.google.com → Admin → Property Settings → Property ID')


if __name__ == '__main__':
    main()
