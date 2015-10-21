from release.platforms import buildbot2bouncer


def treeherder_platform(platform):
    # See https://github.com/mozilla/treeherder/blob/master/ui/js/values.js
    m = {
        "linux": "linux32",
        "linux64": "linux64",
        "macosx64": "osx-10-10",
        "win32": "windowsxp",
        "win64": "windows8-64",
    }
    return m[platform]


def get_complete_mar_url(product, platform, locale, version, buildNumber):
    # TODO: replace bouncer URLs with something stable?
    bouncer_product = "{product}-{version}-complete".format(product=product,
                                                            version=version)
    bouncer_os = buildbot2bouncer(platform)
    return "http://download.mozilla.org/?product={bouncer_product}&" \
        "os={bouncer_os}&lang={locale}".format(bouncer_product=bouncer_product,
                                               bouncer_os=bouncer_os,
                                               locale=locale)
