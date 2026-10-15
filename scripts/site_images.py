"""Images carried over from the Jimdo site.

name -> (local file, [URL candidates]). The last candidate is the exact URL used on
the Jimdo page today (known to work); earlier ones ask Jimdo for a larger version.
"""
_B = "https://image.jimcdn.com/app/cms/image/transf/"
_P = "/path/s167af6fefefc664a/image/"


def _v(img_id, version, ext, *transforms):
    return [_B + t + _P + f"{img_id}/version/{version}/image.{ext}" for t in transforms]


IMAGES = {
    "mark": ("mark.png", []),
    "x-lake": ("x-lake.jpg", []),      # from the @Doi_Lab X header
    "x-islands": ("x-islands.jpg", []),  # from the @Doi_Lab X profile
    "photo-lake": ("photo-lake.jpg", []),
    "photo-tidalflat": ("photo-tidalflat.jpg", []),
    "photo-server": ("photo-server.jpg", []),
    "photo-flasks": ("photo-flasks.jpg", []),
    "photo-sunset": ("photo-sunset.jpg", []),
    "favicon": ("favicon-64.png", []),
    "touch-icon": ("apple-touch-icon.png", []),  # network mark cut from the lab logo (kept in the repo)
    "logo": ("logo.png", _v("i16238ec03dcce5ee", "1733832875", "png",
                            "dimension=800x10000:format=png", "dimension=398x10000:format=png")),
    "portrait": ("portrait.jpg", _v("i73f96505cbf2e42b", "1545962031", "jpg",
                                    "dimension=900x10000:format=jpg", "dimension=342x10000:format=jpg")),
    "portrait-ja": ("portrait-ja.jpg", _v("idc7c98908aed271c", "1545962022", "jpg",
                                          "dimension=900x10000:format=jpg", "dimension=333x10000:format=jpg")),
    "lab-1": ("lab-1.jpg", _v("i8afecb58bec48315", "1588778891", "jpg",
                              "dimension=1400x10000:format=jpg", "dimension=4096x4096:format=jpg")),
    "lab-2": ("lab-2.jpg", _v("i069348a20c8ba89d", "1588778891", "jpg",
                              "dimension=1400x10000:format=jpg", "dimension=4096x4096:format=jpg")),
    "lab-3": ("lab-3.jpg", _v("i8e5fbdea7003a0cd", "1588778891", "jpg",
                              "dimension=1400x10000:format=jpg:rotate=180",
                              "dimension=4096x4096:format=jpg:rotate=180")),
    "lab-4": ("lab-4.jpg", _v("ia2f6bc3464e6955a", "1588778891", "jpg",
                              "dimension=1400x10000:format=jpg", "dimension=4096x4096:format=jpg")),
    "gcb-cover": ("gcb-cover.jpg", _v("i2decd566ba7aac21", "1417264528", "jpg",
                                      "dimension=600x10000:format=jpg", "none")),
    "radioisotopes": ("radioisotopes.jpg", _v("ifd9ac0bae9e826cc", "1490680760", "jpg",
                                              "dimension=600x10000:format=jpg", "dimension=237x10000:format=jpg")),
}
