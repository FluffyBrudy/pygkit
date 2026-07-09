from pygkit.ui.base import generate_box_model


class TestGenerateBoxModel:
    def test_empty(self):
        result = generate_box_model({})
        assert result["full_width"] == 0
        assert result["full_height"] == 0
        assert result["content_width"] == 0
        assert result["content_height"] == 0

    def test_basic(self):
        result = generate_box_model({"width": 100, "height": 50})
        assert result["full_width"] == 100
        assert result["full_height"] == 50
        assert result["content_width"] == 100
        assert result["content_height"] == 50

    def test_padding(self):
        result = generate_box_model(
            {"width": 100, "height": 50, "padding_x": 5, "padding_y": 5}
        )
        assert result["content_width"] == 90
        assert result["content_height"] == 40
        assert result["left"] == 5
        assert result["top"] == 5

    def test_padding_and_border(self):
        result = generate_box_model(
            {
                "width": 100,
                "height": 50,
                "padding_x": 5,
                "padding_y": 5,
                "border_width": 2,
            }
        )
        assert result["content_width"] == 86
        assert result["content_height"] == 36

    def test_margin(self):
        result = generate_box_model(
            {"width": 100, "height": 50, "margin_x": 10, "margin_y": 20}
        )
        assert result["offset_x"] == 10
        assert result["offset_y"] == 20
