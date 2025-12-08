import json
import io
import requests

from itertools import cycle
from panoptes_client import Subject

from .lists import is_list_like


GLYPHS = (
    ("white", "circle"),
    ("red", "square"),
)


def create_subject(project, thumbnail_image, lc_json, data_image=None, metadata={}):
    subject = Subject()
    subject.links.project = project
    subject.add_location(thumbnail_image)
    subject.add_location(
        lc_json,
        manual_mimetype="application/json",
    )
    if data_image is not None:
        subject.add_location(data_image)

    subject.metadata.update(metadata)
    subject.save()
    return subject


def lightcurve_to_json(lcs, labels="Lightcurve", glyphs=GLYPHS):
    if not is_list_like(lcs):
        lcs = [lcs]

    if not is_list_like(labels):
        labels = [labels] * len(lcs)

    json_data = []

    for lc, label, (color, glyph) in zip(lcs, labels, cycle(glyphs)):
        json_data.append(
            {
                "seriesData": [
                    {"x": x, "y": y}
                    for (x, y) in zip(lc["midpointMjdTai"], lc["psfFlux"])
                ],
                "seriesOptions": {
                    "color": color,
                    "glyph": glyph,
                    "label": label,
                },
            }
        )

    return json.dumps({"data": json_data})


def lightcurve_to_json_file(*args, **kwargs):
    lc = lightcurve_to_json(*args, **kwargs)
    f = io.StringIO()
    f.write(lc)
    f.seek(0)
    return f


def lasair_obj_to_subject(obj, project, metadata={}, glyphs=GLYPHS):
    lcs = obj["diaSources"]
    metadata = {"object ID": obj}

    # TODO: This is not fully documented; test and see how the URLs are actually returned by the API
    image_urls = obj["cutout_urls"]
    images = [io.BytesIO(requests.get(url).content) for url in image_urls]

    # TODO: Probably want to join the cutouts or something to make data_image

    return create_subject(
        project=project,
        lc_json=lightcurve_to_json_file(lcs, glyphs=glyphs),
        thumbnail_image=images[0],
        data_image=images[0],
        metadata=metadata,
    )
