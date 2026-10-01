import hashlib
import unittest

from config_renderer import (
    BandStyle,
    ConfigRenderError,
    DatasetConfig,
    RgbChannel,
    RgbStyle,
    canonical_identifier,
    render_config,
)


ALLOWED = {"viridis", "RdYlGn", "bone"}


def landsat(identifier="Landsat RGB 2019"):
    return DatasetConfig(
        identifier=identifier,
        path="s3://xcube/users/42/landsat/data.zarr",
        title="Landsat RGB (2019)",
        description="Surface reflectance",
        variables=("red", "green", "blue", "ndvi"),
        bands=(
            BandStyle("red", "bone", 0, 0.5),
            BandStyle("ndvi", "RdYlGn", -1, 1),
            BandStyle("blue", "bone", 0, 0.5),
            BandStyle("green", "bone", 0, 0.5),
        ),
        rgb=RgbStyle(
            red=RgbChannel("red", 0, 0.5),
            green=RgbChannel("green", 0, 0.5),
            blue=RgbChannel("blue", 0, 0.5),
        ),
    )


class ConfigRendererTest(unittest.TestCase):
    def test_canonical_identifier(self):
        self.assertEqual("landsat-rgb-2019", canonical_identifier(" Landsat RGB (2019) "))

    def test_renders_band_and_rgb_xcube_schema(self):
        rendered = render_config([landsat()], ALLOWED)
        self.assertIn('Identifier: "landsat-rgb-2019"', rendered.yaml)
        self.assertIn('Style: "landsat-rgb-2019-style"', rendered.yaml)
        self.assertIn('"ndvi":\n        ColorBar: "RdYlGn"', rendered.yaml)
        self.assertIn('ValueRange: [-1.0, 1.0]', rendered.yaml)
        self.assertIn('"rgb":\n        Red:', rendered.yaml)
        self.assertIn('Variable: "red"', rendered.yaml)
        self.assertEqual(1, rendered.dataset_count)
        self.assertEqual(1, rendered.style_count)

    def test_output_and_hash_are_independent_of_input_order(self):
        first = DatasetConfig(
            identifier="B Dataset",
            path="/data/b.zarr",
            title="B",
            variables=("value",),
            bands=(BandStyle("value", "viridis", 0, 10),),
        )
        second = DatasetConfig(identifier="A Dataset", path="/data/a.zarr", title="A")
        left = render_config([first, second], ["viridis", "bone"])
        right = render_config([second, first], ["bone", "viridis"])
        self.assertEqual(left.yaml, right.yaml)
        self.assertEqual(left.sha256, right.sha256)
        self.assertEqual(hashlib.sha256(left.yaml.encode()).hexdigest(), left.sha256)
        self.assertLess(left.yaml.index('Identifier: "a-dataset"'), left.yaml.index('Identifier: "b-dataset"'))

    def test_rejects_unsupported_color_bar(self):
        record = DatasetConfig(
            identifier="ndvi",
            path="/data/ndvi.zarr",
            title="NDVI",
            variables=("ndvi",),
            bands=(BandStyle("ndvi", "solid_blue", -1, 1),),
        )
        with self.assertRaisesRegex(ConfigRenderError, "unsupported ColorBar solid_blue"):
            render_config([record], ALLOWED)

    def test_rejects_invalid_ranges_and_unknown_rgb_variables(self):
        invalid_range = DatasetConfig(
            identifier="bad-range",
            path="/data/a.zarr",
            title="Bad",
            bands=(BandStyle("x", "viridis", 1, 1),),
        )
        with self.assertRaisesRegex(ConfigRenderError, "min < max"):
            render_config([invalid_range], ALLOWED)

        invalid_rgb = DatasetConfig(
            identifier="bad-rgb",
            path="/data/b.zarr",
            title="Bad RGB",
            variables=("red", "green"),
            rgb=RgbStyle(
                RgbChannel("red", 0, 1),
                RgbChannel("green", 0, 1),
                RgbChannel("blue", 0, 1),
            ),
        )
        with self.assertRaisesRegex(ConfigRenderError, "unknown RGB blue variable blue"):
            render_config([invalid_rgb], ALLOWED)

    def test_rejects_canonical_identifier_collision(self):
        one = DatasetConfig("Dataset One", "/data/1.zarr", "One")
        two = DatasetConfig("dataset-one", "/data/2.zarr", "Two")
        with self.assertRaisesRegex(ConfigRenderError, "collide"):
            render_config([one, two], ALLOWED)

    def test_empty_config_is_stable(self):
        rendered = render_config([], ALLOWED)
        self.assertEqual("Datasets: []\nStyles: []\n", rendered.yaml)
        self.assertEqual(0, rendered.dataset_count)
        self.assertEqual(0, rendered.style_count)


if __name__ == "__main__":
    unittest.main()
