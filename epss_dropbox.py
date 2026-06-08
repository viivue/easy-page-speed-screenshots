import os

try:
    import dropbox
    from dropbox.files import WriteMode
    from dropbox.exceptions import ApiError
    from dropbox.sharing import SharedLinkSettings, RequestedVisibility
    import dropbox.common as dbx_common
    _dropbox_available = True
except ImportError:
    _dropbox_available = False


def epss_make_dropbox_client():
    """Return a refresh-token-backed Dropbox client, or None if not configured or unavailable."""
    if not _dropbox_available:
        return None
    app_key = os.environ.get("DROPBOX_APP_KEY")
    app_secret = os.environ.get("DROPBOX_APP_SECRET")
    refresh_token = os.environ.get("DROPBOX_REFRESH_TOKEN")
    if not (app_key and app_secret and refresh_token):
        return None

    dbx = dropbox.Dropbox(
        oauth2_refresh_token=refresh_token,
        app_key=app_key,
        app_secret=app_secret,
    )

    # Only for Dropbox Business "team space" roots (see README Notes).
    ns = os.environ.get("DROPBOX_PATH_ROOT_NS")
    if ns:
        dbx = dbx.with_path_root(dbx_common.PathRoot.root(ns))
    return dbx


def epss_upload_and_link(dbx, local_path, dropbox_folder, subfolder):
    """Upload one file and return a shared link. Nested paths auto-create folders."""
    name = os.path.basename(local_path)
    folder = "/" + "/".join(p.strip("/") for p in [dropbox_folder, subfolder] if p)
    dropbox_path = f"{folder}/{name}"

    with open(local_path, "rb") as f:
        dbx.files_upload(f.read(), dropbox_path, mode=WriteMode("overwrite"), mute=True)

    settings = SharedLinkSettings(requested_visibility=RequestedVisibility.public) if _dropbox_available else None
    try:
        return dbx.sharing_create_shared_link_with_settings(dropbox_path, settings=settings).url
    except ApiError as e:
        # Reuse the existing link if this file was shared before.
        try:
            if e.error.is_shared_link_already_exists():
                links = dbx.sharing_list_shared_links(
                    path=dropbox_path, direct_only=True
                ).links
                if links:
                    return links[0].url
        except Exception:
            pass
        raise
