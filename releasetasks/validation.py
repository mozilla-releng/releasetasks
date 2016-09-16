from voluptuous import Schema, Required, Any, Optional, Match
from voluptuous.validators import Url

BASE_SCHEMA = {
    Required('appVersion'): Match('REGEX FOR APPVERSION'),
    Required('balrog_api_root'): Url(),  # Must be an url
    Required('balrog_password'): str,
    Required('balrog_username'): str,
    Required('beetmover_aws_access_key_id'): str,
    Required('beetmover_aws_secret_access_key'): str,
    Required('beetmover_candidates_bucket'): str,
    Required('bouncer_enabled'): bool,
    Required('branch'): str,
    Required('buildNumber'): int,
    Required('build_tools_repo_path'): str,
    Required('checksums_enabled'): bool,
    Required('en_US_config'): {
        'platforms': {
            str: {
                'task_id': str
            }
        }},
    Required('final_verify_channels'): [str],
    Required('final_verify_platforms'): [str],
    Required('uptake_monitoring_platforms'): [str],
    Required('funsize_balrog_api_root'): Url(),
    Required('l10n_changesets'): {
        str: str
    },
    Required('l10n_config'): Any({}, {
        'platforms': {
            str: {
                'en_us_binary_url': str,
                'locales': [str],
                'chunks': int
            }
        },
        'changesets': {
            str: str
        }
    }),
    Required('mozharness_changeset'): str,
    Required('next_version'): Match('REGEX FOR NEXT_VERSION'),
    Required('partial_updates'): {
        str: {
            'buildNumber': int,
            'locales': [str]
        }},
    Required('partner_repacks_platforms'): [str],
    Required('postrelease_bouncer_aliases_enabled'): bool,
    Required('uptake_monitoring_enabled'): bool,
    Required('postrelease_version_bump_enabled'): bool,
    Required('product'): str,
    Required('public_key'): str,
    Optional('push_to_candidates_enabled'): bool,
    Required('push_to_releases_automatic'): bool,
    Required('push_to_releases_enabled'): bool,
    Required('publish_to_balrog_channels'): Any(None, [str]),
    Required('release_channels'): [str],
    Required('repo_path'): str,
    Required('revision'): str,
    Required('signing_class'): str,  # Actually required
    Required('signing_pvt_key'): str,
    Required('source_enabled'): bool,
    Required('tuxedo_server_url'): str,  # Must be an url
    Required('update_verify_enabled'): bool,
    Required('updates_builder_enabled'): bool,
    Optional('updates_enabled'): bool,
    Required('verifyConfigs'): dict,
    Required('version'): Match('REGEX FOR PRODUCT VERSION'),
    Required('publish_to_balrog_channels'): Any(None, [str]),
    Optional('extra_balrog_submitter_params'): dict,
}

FUNSIZE_SCHEMA = {
    Required('updates_enabled'): bool,
    Required('now'): int,
    Required('never'): int,
    Required('branch'): str,
    Required('revision'): str,
    Required('pushlog_id'): str,
    Required('version'): Match('REGEX FOR PRODUCT VERSION'),
    Required('product'): str,
    Required('repo_path'): str
}

BEETMOVE_IMAGE_SCHEMA = {
    Required('push_to_candidates_enabled'): bool,
    Required('now'): int,
    Required('never'): int,
    Required('branch'): str,
    Required('revision'): str,
    Required('pushlog_id'): str,
    Required('version'): Match('REGEX FOR PRODUCT VERSION'),
    Required('product'): str,
    Required('repo_path'): str
}

ENUS_SCHEMA = {
    Required('en_us_config'): {
        'platforms': {
            'task_id': str
        }
    }
}


def validate_kwargs(input_kwargs):
    schema = Schema(BASE_SCHEMA)

    return schema(input_kwargs)
